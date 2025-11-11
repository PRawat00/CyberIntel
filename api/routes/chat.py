"""Chat API endpoints with WebSocket support for Phase 5."""

import logging

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from api.middleware.auth import RequireAuth, User
from database.context_manager import get_context_manager
from database.db import (
    clear_session_context,
    get_db_session,
    get_session_dependencies,
    mark_context_injected,
    record_message_context_usage,
    update_session_context,
)
from database.models import ChatMessage, ChatSession, Scan
from llm_engine.unified_chat_model import UnifiedChatModel, get_unified_chat_model

logger = logging.getLogger(__name__)


# Initialize chat model (singleton pattern)
def get_chat_model() -> UnifiedChatModel:
    """Get or create unified chat model instance."""
    return get_unified_chat_model()


# Pydantic models for request/response
class CreateSessionRequest(BaseModel):
    """Request model for creating a chat session."""

    scan_id: int | None = Field(
        None, description="Scan ID for project-specific chat (null for general)"
    )
    title: str | None = Field(None, description="Optional session title", max_length=255)


class SessionResponse(BaseModel):
    """Response model for chat session."""

    id: int
    scan_id: int | None
    title: str | None
    session_type: str
    created_at: str
    last_message_at: str
    message_count: int


class MessageRequest(BaseModel):
    """Request model for sending a chat message."""

    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    stream: bool = Field(False, description="Whether to stream the response")


class MessageResponse(BaseModel):
    """Response model for chat message."""

    id: int
    session_id: int
    role: str
    content: str
    context_cves: list[str] | None
    created_at: str


# Create router
router = APIRouter(prefix="/api/chat", tags=["Chat"])


# REST Endpoints


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest, user: User = RequireAuth):
    """Create a new chat session.

    Args:
        request: Session creation parameters
        user: Authenticated user

    Returns:
        Created session

    Requires authentication. Created session is owned by the authenticated user.

    Examples:
        ```bash
        # Create project-specific chat
        curl -X POST http://localhost:8000/api/chat/sessions \\
          -H "Content-Type: application/json" \\
          -H "Authorization: Bearer {token}" \\
          -d '{"scan_id": 42, "title": "React App Vulnerabilities"}'

        # Create general chat
        curl -X POST http://localhost:8000/api/chat/sessions \\
          -H "Content-Type: application/json" \\
          -H "Authorization: Bearer {token}" \\
          -d '{"title": "General CVE Questions"}'
        ```
    """
    try:
        with get_db_session() as session:
            # Validate scan exists if scan_id provided
            if request.scan_id:
                scan = session.query(Scan).filter(Scan.id == request.scan_id).first()
                if not scan:
                    raise HTTPException(status_code=404, detail=f"Scan {request.scan_id} not found")

                # Validate scan ownership
                if scan.user_id != user.id:
                    raise HTTPException(
                        status_code=403, detail="Access denied: You don't own this scan"
                    )

            # Create chat session with user_id
            chat_session = ChatSession(
                scan_id=request.scan_id,
                title=request.title,
                session_type="project" if request.scan_id else "general",
                user_id=user.id,
            )

            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)

            logger.info(f"Created chat session {chat_session.id}")

            return SessionResponse(**chat_session.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(  # noqa: B904
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    scan_id: int | None = Query(None, description="Filter by scan ID"),
    limit: int = Query(50, description="Maximum number of sessions to return", ge=1, le=100),
    user: User = RequireAuth,
):
    """List chat sessions for the authenticated user.

    Args:
        scan_id: Optional scan ID filter
        limit: Maximum number of sessions
        user: Authenticated user

    Returns:
        List of sessions owned by the authenticated user

    Requires authentication. Only returns sessions owned by the current user.

    Examples:
        ```bash
        # Get all sessions
        curl http://localhost:8000/api/chat/sessions \\
          -H "Authorization: Bearer {token}"

        # Get sessions for specific scan
        curl http://localhost:8000/api/chat/sessions?scan_id=42 \\
          -H "Authorization: Bearer {token}"
        ```
    """
    try:
        with get_db_session() as session:
            # Filter by user_id first
            query = session.query(ChatSession).filter(ChatSession.user_id == user.id)

            if scan_id:
                query = query.filter(ChatSession.scan_id == scan_id)

            sessions = query.order_by(ChatSession.last_message_at.desc()).limit(limit).all()

            return [SessionResponse(**s.to_dict()) for s in sessions]

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(  # noqa: B904
            status_code=500, detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, user: User = RequireAuth):
    """Get a specific chat session.

    Args:
        session_id: Session ID
        user: Authenticated user

    Returns:
        Session details

    Requires authentication and validates session ownership.
    """
    try:
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()

            if not chat_session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            # Validate ownership
            if chat_session.user_id != user.id:
                raise HTTPException(
                    status_code=403, detail="Access denied: You don't own this session"
                )

            return SessionResponse(**chat_session.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(  # noqa: B904
            status_code=500, detail=f"Failed to get session: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: int,
    limit: int = Query(100, description="Maximum number of messages", ge=1, le=500),
    user: User = RequireAuth,
):
    """Get messages for a chat session.

    Args:
        session_id: Session ID
        limit: Maximum number of messages
        user: Authenticated user

    Returns:
        List of messages

    Requires authentication and validates session ownership.

    Examples:
        ```bash
        curl http://localhost:8000/api/chat/sessions/1/messages \\
          -H "Authorization: Bearer {token}"
        ```
    """
    try:
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()

            if not chat_session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            # Validate ownership
            if chat_session.user_id != user.id:
                raise HTTPException(
                    status_code=403, detail="Access denied: You don't own this session"
                )

            messages = (
                session.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
                .limit(limit)
                .all()
            )

            return [MessageResponse(**m.to_dict()) for m in messages]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(  # noqa: B904
            status_code=500, detail=f"Failed to get messages: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, user: User = RequireAuth):
    """Delete a chat session and all its messages.

    Args:
        session_id: Session ID
        user: Authenticated user

    Returns:
        Success message

    Requires authentication and validates session ownership.
    """
    try:
        with get_db_session() as session:
            chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()

            if not chat_session:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            # Validate ownership
            if chat_session.user_id != user.id:
                raise HTTPException(
                    status_code=403, detail="Access denied: You don't own this session"
                )

            session.delete(chat_session)
            session.commit()

            logger.info(f"Deleted chat session {session_id}")

            return {"message": f"Session {session_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(  # noqa: B904
            status_code=500, detail=f"Failed to delete session: {str(e)}"
        )


# WebSocket Endpoint


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time chat.

    Args:
        websocket: WebSocket connection
        session_id: Chat session ID

    Protocol:
        Client sends:
            {"type": "message", "content": "user message", "dependency_ids": [1,2,3]}  # Optional dependency context
            {"type": "set_context", "dependency_ids": [1,2,3]}  # Update context without sending message
            {"type": "clear_context"}  # Clear dependency context

        Server sends:
            {"type": "start"}  # Message generation started
            {"type": "chunk", "content": "text chunk"}  # Streaming chunks
            {"type": "end", "message_id": 123}  # Message complete
            {"type": "error", "error": "error message"}  # Error occurred
            {"type": "context_updated"}  # Context was updated
            {"type": "context_cleared"}  # Context was cleared

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/api/chat/ws/1?token=YOUR_JWT_TOKEN');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chunk') {
                console.log(data.content);
            }
        };

        ws.send(JSON.stringify({
            type: 'message',
            content: 'What are the critical vulnerabilities?'
        }));
        ```
    """
    await websocket.accept()
    logger.info(f"WebSocket connection attempt for session {session_id}")

    try:
        # Authenticate user via query parameter token
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json(
                {"type": "error", "error": "Authentication required - missing token"}
            )
            await websocket.close(code=1008, reason="Authentication required")
            return

        # Verify token and get user
        from api.middleware.auth import verify_token_get_user

        try:
            user = verify_token_get_user(token)
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.send_json({"type": "error", "error": "Invalid or expired token"})
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Verify session exists and belongs to user
        with get_db_session() as db_session:
            chat_session = (
                db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
            )

            if not chat_session:
                await websocket.send_json(
                    {"type": "error", "error": f"Session {session_id} not found"}
                )
                await websocket.close(code=1008, reason="Session not found")
                return

            # Security: Verify session belongs to authenticated user
            if chat_session.user_id != user.id:
                logger.warning(
                    f"User {user.id} attempted to access session {session_id} owned by {chat_session.user_id}"
                )
                await websocket.send_json(
                    {"type": "error", "error": "Access denied - session does not belong to you"}
                )
                await websocket.close(code=1008, reason="Access denied")
                return

            session_type = chat_session.session_type
            scan_id = chat_session.scan_id

        # Initialize context manager for this session
        context_manager = get_context_manager(session_id)

        # Ensure context has scan_id if it's a project session
        if session_type == "project" and scan_id:
            current_context = context_manager.get_current_context()
            if scan_id not in current_context.scans:
                context_manager.update_context(scans=[scan_id])
                logger.info(
                    f"Initialized project context with scan_id={scan_id} for session {session_id}"
                )

        # Get chat model
        chat_model = get_chat_model()

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            # Handle set_context message
            if message_type == "set_context":
                dependency_ids = data.get("dependency_ids", [])
                if update_session_context(session_id, dependency_ids if dependency_ids else None):
                    await websocket.send_json({"type": "context_updated"})
                    logger.info(
                        f"Updated context for session {session_id}: {len(dependency_ids) if dependency_ids else 0} dependencies"
                    )
                else:
                    await websocket.send_json(
                        {"type": "error", "error": "Failed to update context"}
                    )
                continue

            # Handle clear_context message
            if message_type == "clear_context":
                if clear_session_context(session_id):
                    await websocket.send_json({"type": "context_cleared"})
                    logger.info(f"Cleared context for session {session_id}")
                else:
                    await websocket.send_json({"type": "error", "error": "Failed to clear context"})
                continue

            # Handle regular message
            if message_type != "message":
                await websocket.send_json({"type": "error", "error": "Invalid message type"})
                continue

            user_message = data.get("content", "").strip()

            if not user_message:
                await websocket.send_json({"type": "error", "error": "Empty message"})
                continue

            # Handle dependency_ids in message (for first-time context setting)
            dependency_ids = data.get("dependency_ids")
            if dependency_ids is not None:
                # SECURITY: Validate dependency IDs
                if dependency_ids:  # If not empty list
                    try:
                        # Validate all IDs are integers
                        validated_ids = [int(dep_id) for dep_id in dependency_ids]

                        # Validate user owns these dependencies
                        from database.models import Dependency, Scan

                        with get_db_session() as db_session:
                            # Get user's scan IDs
                            user_scans = (
                                db_session.query(Scan.id).filter(Scan.user_id == user.id).all()
                            )
                            user_scan_ids = [s.id for s in user_scans]

                            # Validate dependencies belong to user's scans
                            valid_deps = (
                                db_session.query(Dependency.id)
                                .filter(
                                    Dependency.id.in_(validated_ids),
                                    Dependency.scan_id.in_(user_scan_ids),
                                )
                                .all()
                            )
                            valid_dep_ids = [d.id for d in valid_deps]

                            if len(valid_dep_ids) != len(validated_ids):
                                logger.warning(
                                    f"SECURITY: User {user.id} attempted to set invalid dependency IDs: "
                                    f"requested {len(validated_ids)}, valid {len(valid_dep_ids)}"
                                )
                                await websocket.send_json(
                                    {
                                        "type": "error",
                                        "error": "Some dependency IDs are invalid or don't belong to you",
                                    }
                                )
                                continue

                            # Update with validated IDs only
                            update_session_context(session_id, valid_dep_ids)
                            logger.info(
                                f"Updated context via message for session {session_id}: {len(valid_dep_ids)} dependencies"
                            )
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid dependency IDs format: {dependency_ids} - {e}")
                        await websocket.send_json(
                            {"type": "error", "error": "Invalid dependency ID format"}
                        )
                        continue
                else:
                    # Empty list - clear dependencies
                    update_session_context(session_id, None)
                    logger.info(f"Cleared dependencies for session {session_id}")

            print(f"\n{'='*80}")
            print(f"🚨 MESSAGE RECEIVED IN SESSION {session_id}")
            print(f"Content: {user_message[:100]}")
            print(f"{'='*80}\n")
            logger.info(f"Received message in session {session_id}: {user_message[:50]}...")

            try:
                # Save user message
                with get_db_session() as db_session:
                    user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
                    db_session.add(user_msg)
                    db_session.commit()

                    # Get conversation history (last 5 messages)
                    history = (
                        db_session.query(ChatMessage)
                        .filter(ChatMessage.session_id == session_id)
                        .order_by(ChatMessage.created_at.desc())
                        .limit(10)
                        .all()
                    )

                    conversation_history = [
                        {"role": msg.role, "content": msg.content}
                        for msg in reversed(history[:-1])  # Exclude the just-added user message
                    ]

                # Get selected dependencies
                selected_deps = get_session_dependencies(session_id)
                logger.info(
                    f"Retrieved {len(selected_deps) if selected_deps else 0} selected dependencies"
                )

                with get_db_session() as db_session:
                    chat_session_obj = (
                        db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
                    )
                    context_injected = (
                        bool(chat_session_obj.context_injected) if chat_session_obj else False
                    )

                # Send start signal
                await websocket.send_json({"type": "start"})

                # Build context for unified chat
                context = context_manager.get_current_context()

                # Update context with conversation history
                context = context.copy(conversation_history=conversation_history)

                # ALWAYS include selected dependencies in context
                # The LLM router will decide whether to use them
                if selected_deps:
                    dependency_ids = [dep.id for dep in selected_deps]
                    context = context.copy(dependencies=dependency_ids)
                    logger.info(
                        f"Added {len(dependency_ids)} dependencies to context (LLM will decide usage)"
                    )

                # Generate response using unified chat model with LLM routing
                logger.info(
                    f"Unified chat with LLM routing: session={session_id}, "
                    f"scans={len(context.scans)}, deps={len(context.dependencies)}, "
                    f"query='{user_message[:50]}...'"
                )

                response_stream = chat_model.chat(query=user_message, context=context, stream=True)

                # Stream chunks to client and collect full response
                full_response = []
                try:
                    for chunk in response_stream:
                        full_response.append(chunk)
                        await websocket.send_json({"type": "chunk", "content": chunk})
                        # Removed typing delay to improve performance
                        # await asyncio.sleep(0.05)
                except StopIteration:
                    # Generator exhausted normally
                    pass
                except Exception as stream_error:
                    logger.error(f"Streaming error: {stream_error}", exc_info=True)
                    await websocket.send_json(
                        {"type": "error", "error": f"Streaming failed: {str(stream_error)}"}
                    )
                    continue  # Skip saving partial response and wait for next message

                assistant_response = "".join(full_response)

                # Mark context as injected if this was the first time with dependencies
                if selected_deps and not context_injected:
                    mark_context_injected(session_id)
                    logger.info(f"Marked context as injected for session {session_id}")

                # Save assistant message
                with get_db_session() as db_session:
                    assistant_msg = ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=assistant_response,
                        rag_query=user_message,
                    )
                    db_session.add(assistant_msg)
                    db_session.commit()
                    db_session.refresh(assistant_msg)

                    # Record context usage for this message
                    if selected_deps:
                        record_message_context_usage(
                            message_id=assistant_msg.id,
                            context_injected=True,  # Always True now - LLM decides usage
                            dependency_count=len(selected_deps),
                        )
                        logger.debug(
                            f"Recorded context usage for message {assistant_msg.id}: "
                            f"injected=True, count={len(selected_deps)}"
                        )

                    message_id = assistant_msg.id

                    # Update session last_message_at
                    db_session.query(ChatSession).filter(ChatSession.id == session_id).update(
                        {"last_message_at": assistant_msg.created_at}
                    )
                    db_session.commit()

                # Send end signal
                await websocket.send_json({"type": "end", "message_id": message_id})

                logger.info(f"Completed message generation for session {session_id}")

            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await websocket.send_json(
                    {"type": "error", "error": f"Failed to generate response: {str(e)}"}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except:  # noqa: E722,S110
            pass
    finally:
        try:
            await websocket.close()
        except:  # noqa: E722,S110
            pass
