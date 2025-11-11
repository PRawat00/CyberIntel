"""Unit tests for Chat REST API endpoints.

Tests the FastAPI REST endpoints for chat session management
including creation, retrieval, listing, and deletion.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.models import ChatMessage, ChatSession, Scan


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session


class TestCreateSession:
    """Test POST /api/chat/sessions endpoint."""

    @patch("api.routes.chat.get_db_session")
    def test_create_general_session(self, mock_get_db, client):
        """Test creating a general chat session."""
        # Setup mock
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        # Mock created session with proper side effect
        def add_side_effect(obj):
            # Set id after add (simulating database auto-increment)
            obj.id = 1
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)
            obj.last_message_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_session.add.side_effect = add_side_effect
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Make request
        response = client.post("/api/chat/sessions", json={"title": "General Questions"})

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["scan_id"] is None
        assert data["title"] == "General Questions"
        assert data["session_type"] == "general"

    @patch("api.routes.chat.get_db_session")
    def test_create_project_session(self, mock_get_db, client):
        """Test creating a project-specific chat session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        # Mock scan exists
        mock_scan = Mock(spec=Scan)
        mock_scan.id = 42
        mock_session.query.return_value.filter.return_value.first.return_value = mock_scan

        # Mock created session with proper side effect
        def add_side_effect(obj):
            obj.id = 2
            obj.created_at = datetime(2025, 1, 9, 10, 0, 0)
            obj.last_message_at = datetime(2025, 1, 9, 10, 0, 0)

        mock_session.add.side_effect = add_side_effect
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Make request
        response = client.post("/api/chat/sessions", json={"scan_id": 42, "title": "Project Chat"})

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == 42
        assert data["session_type"] == "project"

    @patch("api.routes.chat.get_db_session")
    def test_create_session_scan_not_found(self, mock_get_db, client):
        """Test creating session with non-existent scan."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        # Mock scan not found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.post("/api/chat/sessions", json={"scan_id": 999})

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_session_invalid_request(self, client):
        """Test creating session with invalid data."""
        # Missing required fields (none required, but test validation)
        response = client.post("/api/chat/sessions", json={"invalid_field": "value"})

        # Should still succeed (all fields optional)
        assert response.status_code in [200, 422]  # 422 if validation fails


class TestListSessions:
    """Test GET /api/chat/sessions endpoint."""

    @patch("api.routes.chat.get_db_session")
    def test_list_all_sessions(self, mock_get_db, client):
        """Test listing all sessions."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        # Mock sessions
        mock_sessions = [
            Mock(
                to_dict=lambda: {
                    "id": 1,
                    "scan_id": None,
                    "title": "General",
                    "session_type": "general",
                    "created_at": "2025-01-09T10:00:00",
                    "last_message_at": "2025-01-09T10:00:00",
                    "message_count": 5,
                }
            ),
            Mock(
                to_dict=lambda: {
                    "id": 2,
                    "scan_id": 42,
                    "title": "Project",
                    "session_type": "project",
                    "created_at": "2025-01-09T11:00:00",
                    "last_message_at": "2025-01-09T11:00:00",
                    "message_count": 3,
                }
            ),
        ]

        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value.limit.return_value.all.return_value = mock_sessions

        # Make request
        response = client.get("/api/chat/sessions")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2

    @patch("api.routes.chat.get_db_session")
    def test_list_sessions_filtered_by_scan(self, mock_get_db, client):
        """Test listing sessions filtered by scan_id."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_sessions = [
            Mock(
                to_dict=lambda: {
                    "id": 2,
                    "scan_id": 42,
                    "title": "Project",
                    "session_type": "project",
                    "created_at": "2025-01-09T11:00:00",
                    "last_message_at": "2025-01-09T11:00:00",
                    "message_count": 3,
                }
            )
        ]

        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_sessions
        )

        # Make request with filter
        response = client.get("/api/chat/sessions?scan_id=42")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["scan_id"] == 42

    @patch("api.routes.chat.get_db_session")
    def test_list_sessions_empty(self, mock_get_db, client):
        """Test listing sessions when none exist."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        # Make request
        response = client.get("/api/chat/sessions")

        # Verify
        assert response.status_code == 200
        assert response.json() == []


class TestGetSession:
    """Test GET /api/chat/sessions/{session_id} endpoint."""

    @patch("api.routes.chat.get_db_session")
    def test_get_session_success(self, mock_get_db, client):
        """Test getting a specific session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_chat_session = Mock(
            to_dict=lambda: {
                "id": 1,
                "scan_id": None,
                "title": "Test Session",
                "session_type": "general",
                "created_at": "2025-01-09T10:00:00",
                "last_message_at": "2025-01-09T10:00:00",
                "message_count": 5,
            }
        )

        mock_session.query.return_value.filter.return_value.first.return_value = mock_chat_session

        # Make request
        response = client.get("/api/chat/sessions/1")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Session"

    @patch("api.routes.chat.get_db_session")
    def test_get_session_not_found(self, mock_get_db, client):
        """Test getting non-existent session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.get("/api/chat/sessions/999")

        # Verify
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetMessages:
    """Test GET /api/chat/sessions/{session_id}/messages endpoint."""

    @patch("api.routes.chat.get_db_session")
    def test_get_messages_success(self, mock_get_db, client):
        """Test getting messages for a session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        # Mock session exists
        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1

        # Mock messages
        mock_messages = [
            Mock(
                to_dict=lambda: {
                    "id": 1,
                    "session_id": 1,
                    "role": "user",
                    "content": "Hello",
                    "context_cves": None,
                    "created_at": "2025-01-09T10:00:00",
                }
            ),
            Mock(
                to_dict=lambda: {
                    "id": 2,
                    "session_id": 1,
                    "role": "assistant",
                    "content": "Hi there!",
                    "context_cves": ["CVE-2023-1234"],
                    "created_at": "2025-01-09T10:01:00",
                }
            ),
        ]

        # Setup query mock chain
        def query_side_effect(model):
            if model == ChatSession:
                mock_q = Mock()
                mock_q.filter.return_value.first.return_value = mock_chat_session
                return mock_q
            elif model == ChatMessage:
                mock_q = Mock()
                mock_q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    mock_messages
                )
                return mock_q

        mock_session.query.side_effect = query_side_effect

        # Make request
        response = client.get("/api/chat/sessions/1/messages")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"

    @patch("api.routes.chat.get_db_session")
    def test_get_messages_session_not_found(self, mock_get_db, client):
        """Test getting messages for non-existent session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.get("/api/chat/sessions/999/messages")

        # Verify
        assert response.status_code == 404

    @patch("api.routes.chat.get_db_session")
    def test_get_messages_empty(self, mock_get_db, client):
        """Test getting messages when session has none."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_chat_session = Mock(spec=ChatSession)

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

        mock_session.query.side_effect = query_side_effect

        # Make request
        response = client.get("/api/chat/sessions/1/messages")

        # Verify
        assert response.status_code == 200
        assert response.json() == []


class TestDeleteSession:
    """Test DELETE /api/chat/sessions/{session_id} endpoint."""

    @patch("api.routes.chat.get_db_session")
    def test_delete_session_success(self, mock_get_db, client):
        """Test deleting a session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1

        mock_session.query.return_value.filter.return_value.first.return_value = mock_chat_session

        # Make request
        response = client.delete("/api/chat/sessions/1")

        # Verify
        assert response.status_code == 200
        mock_session.delete.assert_called_once_with(mock_chat_session)
        mock_session.commit.assert_called_once()

    @patch("api.routes.chat.get_db_session")
    def test_delete_session_not_found(self, mock_get_db, client):
        """Test deleting non-existent session."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Make request
        response = client.delete("/api/chat/sessions/999")

        # Verify
        assert response.status_code == 404
        mock_session.delete.assert_not_called()


class TestQueryParameters:
    """Test query parameter validation."""

    @patch("api.routes.chat.get_db_session")
    def test_list_sessions_with_limit(self, mock_get_db, client):
        """Test limit parameter."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_query = mock_session.query.return_value
        mock_query.order_by.return_value.limit.return_value.all.return_value = []

        # Make request with limit
        response = client.get("/api/chat/sessions?limit=10")

        # Verify
        assert response.status_code == 200

    def test_list_sessions_invalid_limit(self, client):
        """Test invalid limit parameter."""
        # Limit too high
        response = client.get("/api/chat/sessions?limit=1000")
        assert response.status_code == 422  # Validation error

        # Limit too low
        response = client.get("/api/chat/sessions?limit=0")
        assert response.status_code == 422

    @patch("api.routes.chat.get_db_session")
    def test_get_messages_with_limit(self, mock_get_db, client):
        """Test limit parameter for messages."""
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_chat_session = Mock(spec=ChatSession)

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

        mock_session.query.side_effect = query_side_effect

        # Make request with limit
        response = client.get("/api/chat/sessions/1/messages?limit=50")

        # Verify
        assert response.status_code == 200
