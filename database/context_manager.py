"""
Session Context Manager for dynamic context handling.

Manages the context stack for chat sessions, enabling dynamic context changes
mid-conversation with rollback support.
"""

import json
import logging

from database.db import get_db_session
from database.models import ChatSession
from llm_engine.chat_context import ChatContext, ContextUpdate

logger = logging.getLogger(__name__)


class SessionContextManager:
    """
    Manages context for a chat session.

    Features:
    - Context stack with push/pop (rollback support)
    - Persistence to database
    - History tracking
    - Dynamic updates mid-conversation
    """

    def __init__(self, session_id: int):
        """
        Initialize context manager for a session.

        Args:
            session_id: Chat session ID
        """
        self.session_id = session_id
        self.context_stack: list[ChatContext] = []
        self._load_from_database()

    def _load_from_database(self):
        """Load context stack from database."""
        with get_db_session() as session:
            chat_session = (
                session.query(ChatSession).filter(ChatSession.id == self.session_id).first()
            )

            if not chat_session:
                raise ValueError(f"Session {self.session_id} not found")

            # Load context stack from database
            if chat_session.context_stack:
                try:
                    stack_data = (
                        json.loads(chat_session.context_stack)
                        if isinstance(chat_session.context_stack, str)
                        else chat_session.context_stack
                    )

                    self.context_stack = [
                        ChatContext.from_dict(ctx_data) for ctx_data in stack_data
                    ]
                    logger.info(
                        f"Loaded {len(self.context_stack)} contexts for session {self.session_id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to load context stack: {e}", exc_info=True)
                    self.context_stack = []

            # If no context stack, create initial context
            if not self.context_stack:
                initial_context = ChatContext(
                    session_id=self.session_id, user_id=chat_session.user_id or "unknown"
                )

                # Migrate old-style context if exists
                if chat_session.selected_dependency_ids:
                    initial_context.dependencies = chat_session.selected_dependency_ids

                # Try to infer scan from old schema
                if hasattr(chat_session, "scan_id") and chat_session.scan_id:
                    initial_context.scans = [chat_session.scan_id]

                # Load enabled features if exists
                if chat_session.enabled_features:
                    try:
                        features = (
                            json.loads(chat_session.enabled_features)
                            if isinstance(chat_session.enabled_features, str)
                            else chat_session.enabled_features
                        )
                        initial_context.enabled_features = set(features)
                    except Exception:  # noqa: S110
                        pass

                self.context_stack = [initial_context]
                self._persist()

    def _persist(self):
        """Save context stack to database."""
        try:
            stack_data = [ctx.to_dict() for ctx in self.context_stack]

            with get_db_session() as session:
                chat_session = (
                    session.query(ChatSession).filter(ChatSession.id == self.session_id).first()
                )

                if chat_session:
                    chat_session.context_stack = json.dumps(stack_data)
                    session.commit()
                    logger.debug(f"Persisted context stack for session {self.session_id}")

        except Exception as e:
            logger.error(f"Failed to persist context stack: {e}", exc_info=True)

    def get_current_context(self) -> ChatContext:
        """
        Get the current (top of stack) context.

        Returns:
            Current ChatContext
        """
        if not self.context_stack:
            raise ValueError("Context stack is empty")

        return self.context_stack[-1]

    def push_context(self, update: ContextUpdate):
        """
        Push a new context layer onto the stack.

        Creates a new context by merging the update with the current context.

        Args:
            update: Context update to apply
        """
        current = self.get_current_context()
        new_context = current.merge(update)
        self.context_stack.append(new_context)
        self._persist()

        logger.info(
            f"Pushed context for session {self.session_id}. Stack depth: {len(self.context_stack)}"
        )

    def pop_context(self) -> bool:
        """
        Pop the top context from the stack (rollback).

        Returns:
            True if popped successfully, False if only one context remains
        """
        if len(self.context_stack) <= 1:
            logger.warning(f"Cannot pop - only one context remains for session {self.session_id}")
            return False

        self.context_stack.pop()
        self._persist()

        logger.info(
            f"Popped context for session {self.session_id}. Stack depth: {len(self.context_stack)}"
        )
        return True

    def update_context(self, **updates):
        """
        Update the current context in-place.

        Args:
            **updates: Fields to update
        """
        current = self.get_current_context()
        updated = current.copy(**updates)
        self.context_stack[-1] = updated
        self._persist()

        logger.info(f"Updated current context for session {self.session_id}")

    def replace_context(self, new_context: ChatContext):
        """
        Replace the current context entirely.

        Args:
            new_context: New context to use
        """
        if not self.context_stack:
            self.context_stack = [new_context]
        else:
            self.context_stack[-1] = new_context

        self._persist()
        logger.info(f"Replaced current context for session {self.session_id}")

    def clear_stack(self):
        """Clear the context stack and create a fresh context."""
        with get_db_session() as session:
            chat_session = (
                session.query(ChatSession).filter(ChatSession.id == self.session_id).first()
            )

            user_id = chat_session.user_id if chat_session else "unknown"

        fresh_context = ChatContext(session_id=self.session_id, user_id=user_id)

        self.context_stack = [fresh_context]
        self._persist()

        logger.info(f"Cleared context stack for session {self.session_id}")

    def get_stack_depth(self) -> int:
        """Get the current depth of the context stack."""
        return len(self.context_stack)

    def get_history(self) -> list[ChatContext]:
        """Get full context history (all layers)."""
        return self.context_stack.copy()


# Cache of context managers to avoid recreating
_context_manager_cache = {}


def get_context_manager(session_id: int) -> SessionContextManager:
    """
    Get or create a context manager for a session.

    Args:
        session_id: Chat session ID

    Returns:
        SessionContextManager instance
    """
    if session_id not in _context_manager_cache:
        _context_manager_cache[session_id] = SessionContextManager(session_id)

    return _context_manager_cache[session_id]


def clear_context_manager_cache(session_id: int | None = None):
    """
    Clear context manager cache.

    Args:
        session_id: Specific session to clear, or None to clear all
    """
    global _context_manager_cache

    if session_id is not None:
        _context_manager_cache.pop(session_id, None)
        logger.debug(f"Cleared context manager cache for session {session_id}")
    else:
        _context_manager_cache.clear()
        logger.debug("Cleared all context manager caches")
