"""Unit tests for Chat WebSocket functionality.

Tests the WebSocket endpoint for real-time chat including
message handling, streaming, and error scenarios.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.models import ChatMessage, ChatSession


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWebSocketConnection:
    """Test WebSocket connection establishment."""

    @patch("api.routes.chat.get_db_session")
    @patch("api.routes.chat.get_chat_model")
    def test_successful_connection(self, mock_get_model, mock_get_db, client):
        """Test successful WebSocket connection."""
        # Mock session exists
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"
        mock_chat_session.scan_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_chat_session

        # Connect to WebSocket
        with client.websocket_connect("/api/chat/ws/1") as websocket:
            # Connection should be established
            assert websocket is not None

    @patch("api.routes.chat.get_db_session")
    def test_connection_session_not_found(self, mock_get_db, client):
        """Test WebSocket connection with non-existent session."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Session not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with client.websocket_connect("/api/chat/ws/999") as websocket:
            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "not found" in data["error"].lower()


class TestWebSocketMessaging:
    """Test WebSocket message handling."""

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_send_message_general_chat(self, mock_get_db, mock_get_model, client):
        """Test sending a message in general chat."""
        # Setup database mocks
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"
        mock_chat_session.scan_id = None

        # Mock message queries
        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                # No history
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    []
                )
                # Update query
                mock_q.filter.return_value.update.return_value = None
                return mock_q

        mock_db.query.side_effect = query_side_effect

        # Mock message add/commit
        def add_side_effect(obj):
            obj.id = 1
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_db.add.side_effect = add_side_effect
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock chat model
        mock_model = Mock()
        mock_model.chat_general.return_value = iter(["Hello ", "world!"])
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            # Send message
            websocket.send_json({"type": "message", "content": "Test message"})

            # Receive start signal
            data = websocket.receive_json()
            assert data["type"] == "start"

            # Receive chunks
            chunks = []
            while True:
                data = websocket.receive_json()
                if data["type"] == "chunk":
                    chunks.append(data["content"])
                elif data["type"] == "end":
                    assert "message_id" in data
                    break

            assert chunks == ["Hello ", "world!"]

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_send_message_project_chat(self, mock_get_db, mock_get_model, client):
        """Test sending a message in project chat."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "project"
        mock_chat_session.scan_id = 42

        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    []
                )
                mock_q.filter.return_value.update.return_value = None
                return mock_q

        mock_db.query.side_effect = query_side_effect

        def add_side_effect(obj):
            obj.id = 1
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_db.add.side_effect = add_side_effect

        # Mock chat model - should call chat_project
        mock_model = Mock()
        mock_model.chat_project.return_value = iter(["Project ", "response"])
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            websocket.send_json({"type": "message", "content": "What are my vulnerabilities?"})

            # Skip to end
            while True:
                data = websocket.receive_json()
                if data["type"] == "end":
                    break

            # Verify chat_project was called (not chat_general)
            mock_model.chat_project.assert_called_once()
            mock_model.chat_general.assert_not_called()

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_send_empty_message(self, mock_get_db, mock_get_model, client):
        """Test sending empty message returns error."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"
        mock_chat_session.scan_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_chat_session

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            # Send empty message
            websocket.send_json({"type": "message", "content": ""})

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "empty" in data["error"].lower()

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_send_invalid_message_type(self, mock_get_db, mock_get_model, client):
        """Test sending invalid message type."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_chat_session

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            # Send invalid type
            websocket.send_json({"type": "invalid", "content": "test"})

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "invalid" in data["error"].lower()


class TestConversationHistory:
    """Test conversation history handling."""

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_message_with_conversation_history(self, mock_get_db, mock_get_model, client):
        """Test that conversation history is passed to chat model."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"
        mock_chat_session.scan_id = None

        # Mock existing conversation history
        # mock_msg1 = Mock(role="user", content="Previous question")
        # mock_msg2 = Mock(role="assistant", content="Previous answer")

        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                # Return history (reversed because we reverse it in code)
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                    Mock(role="assistant", content="Previous answer"),
                    Mock(role="user", content="Previous question"),
                ]
                mock_q.filter.return_value.update.return_value = None
                return mock_q

        mock_db.query.side_effect = query_side_effect

        def add_side_effect(obj):
            obj.id = 1
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_db.add.side_effect = add_side_effect

        mock_model = Mock()
        mock_model.chat_general.return_value = iter(["Response"])
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            websocket.send_json({"type": "message", "content": "Follow-up question"})

            # Wait for end
            while True:
                data = websocket.receive_json()
                if data["type"] == "end":
                    break

            # Verify conversation history was passed
            call_args = mock_model.chat_general.call_args
            assert call_args[1]["conversation_history"] is not None
            # Should have previous messages
            assert len(call_args[1]["conversation_history"]) > 0


class TestErrorHandling:
    """Test error handling in WebSocket."""

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_chat_model_error(self, mock_get_db, mock_get_model, client):
        """Test handling of chat model errors."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"

        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    []
                )
                return mock_q

        mock_db.query.side_effect = query_side_effect

        def add_side_effect(obj):
            obj.id = 1

        mock_db.add.side_effect = add_side_effect

        # Mock chat model raises error
        mock_model = Mock()
        mock_model.chat_general.side_effect = Exception("Model Error")
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            websocket.send_json({"type": "message", "content": "Test"})

            # Should receive start then error
            data = websocket.receive_json()
            assert data["type"] == "start"

            data = websocket.receive_json()
            assert data["type"] == "error"

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_streaming_error(self, mock_get_db, mock_get_model, client):
        """Test handling of streaming errors."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"

        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    []
                )
                return mock_q

        mock_db.query.side_effect = query_side_effect

        def add_side_effect(obj):
            obj.id = 1

        mock_db.add.side_effect = add_side_effect

        # Mock streaming that raises error mid-stream
        def error_generator():
            yield "Hello"
            raise Exception("Stream Error")

        mock_model = Mock()
        mock_model.chat_general.return_value = error_generator()
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            websocket.send_json({"type": "message", "content": "Test"})

            # Should receive start
            data = websocket.receive_json()
            assert data["type"] == "start"

            # Should receive first chunk
            data = websocket.receive_json()
            assert data["type"] == "chunk"

            # Should receive error
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "streaming" in data["error"].lower() or "failed" in data["error"].lower()


class TestMultipleMessages:
    """Test sending multiple messages in same connection."""

    @patch("api.routes.chat.get_chat_model")
    @patch("api.routes.chat.get_db_session")
    def test_send_multiple_messages(self, mock_get_db, mock_get_model, client):
        """Test sending multiple messages sequentially."""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.session_type = "general"

        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    []
                )
                mock_q.filter.return_value.update.return_value = None
                return mock_q

        mock_db.query.side_effect = query_side_effect

        call_count = [0]

        def add_side_effect(obj):
            call_count[0] += 1
            obj.id = call_count[0]
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_db.add.side_effect = add_side_effect

        mock_model = Mock()
        mock_model.chat_general.side_effect = [
            iter(["First ", "response"]),
            iter(["Second ", "response"]),
        ]
        mock_get_model.return_value = mock_model

        with client.websocket_connect("/api/chat/ws/1") as websocket:
            # Send first message
            websocket.send_json({"type": "message", "content": "First question"})

            # Wait for completion
            while True:
                data = websocket.receive_json()
                if data["type"] == "end":
                    break

            # Send second message
            websocket.send_json({"type": "message", "content": "Second question"})

            # Wait for completion
            while True:
                data = websocket.receive_json()
                if data["type"] == "end":
                    break

            # Both messages should have been processed
            assert mock_model.chat_general.call_count == 2
