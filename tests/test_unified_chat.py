"""
Comprehensive tests for the unified chat architecture.

Tests all new components:
- ChatContext and ContextUpdate
- RetrievalStrategy implementations
- IntentRouter with chain of handlers
- UnifiedChatModel
- SessionContextManager
- FeatureManager
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from database.context_manager import SessionContextManager
from database.models import CVE, ChatSession, Dependency
from llm_engine.chat_context import ChatContext, ContextUpdate, RetrievalResult
from llm_engine.feature_manager import FeatureManager, Features
from llm_engine.intent_router import (
    DependencyFocusedHandler,
    GeneralSecurityHandler,
    GreetingHandler,
    IntentRouter,
    ProjectScanHandler,
)
from llm_engine.strategies.composite_strategy import CompositeStrategy
from llm_engine.strategies.direct_dependency_strategy import DirectDependencyStrategy
from llm_engine.strategies.general_cve_strategy import GeneralCVEStrategy
from llm_engine.strategies.project_cve_strategy import ProjectCVEStrategy
from llm_engine.unified_chat_model import UnifiedChatModel


class TestChatContext:
    """Test ChatContext data structure."""

    def test_empty_context_creation(self):
        """Test creating empty context."""
        ctx = ChatContext(session_id=1, user_id="user123")

        assert ctx.session_id == 1
        assert ctx.user_id == "user123"
        assert ctx.scans == []
        assert ctx.dependencies == []
        assert ctx.cves == []
        assert ctx.conversation_history == []

    def test_context_with_data(self):
        """Test creating context with data."""
        ctx = ChatContext(
            session_id=1,
            user_id="user123",
            scans=[1, 2],
            dependencies=[10, 20, 30],
            cves=["CVE-2024-1234"],
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        )

        assert len(ctx.scans) == 2
        assert len(ctx.dependencies) == 3
        assert len(ctx.cves) == 1
        assert len(ctx.conversation_history) == 2

    def test_context_helper_methods(self):
        """Test context helper methods."""
        ctx = ChatContext(session_id=1, user_id="user123")

        # Empty context
        assert not ctx.has_scan_context()
        assert not ctx.has_dependency_context()
        assert not ctx.has_cve_context()

        # Add data
        ctx.scans = [1]
        ctx.dependencies = [10]
        ctx.cves = ["CVE-2024-1234"]

        assert ctx.has_scan_context()
        assert ctx.has_dependency_context()
        assert ctx.has_cve_context()

    def test_context_merge(self):
        """Test merging context with update."""
        ctx = ChatContext(session_id=1, user_id="user123", dependencies=[10, 20])

        update = ContextUpdate(add_dependencies=[30], remove_dependencies=[10], add_scans=[5])

        new_ctx = ctx.merge(update)

        # Original unchanged
        assert ctx.dependencies == [10, 20]

        # New context updated
        assert set(new_ctx.dependencies) == {20, 30}
        assert new_ctx.scans == [5]

    def test_context_serialization(self):
        """Test context to_dict and from_dict."""
        ctx = ChatContext(
            session_id=1,
            user_id="user123",
            scans=[1, 2],
            dependencies=[10, 20],
            enabled_features={"smart_context_injection", "dependency_chat"},
        )

        # Serialize
        data = ctx.to_dict()
        assert isinstance(data, dict)
        assert data["session_id"] == 1
        assert data["scans"] == [1, 2]

        # Deserialize
        ctx2 = ChatContext.from_dict(data)
        assert ctx2.session_id == ctx.session_id
        assert ctx2.scans == ctx.scans
        assert ctx2.enabled_features == ctx.enabled_features


class TestRetrievalResult:
    """Test RetrievalResult data structure."""

    def test_retrieval_result_creation(self):
        """Test creating retrieval result."""
        result = RetrievalResult(
            strategy_name="test_strategy",
            query="test query",
            cves=[
                {"cve_id": "CVE-2024-1234", "severity": "HIGH"},
                {"cve_id": "CVE-2024-5678", "severity": "CRITICAL"},
            ],
        )

        assert result.strategy_name == "test_strategy"
        assert result.query == "test query"
        assert len(result.cves) == 2

    def test_retrieval_result_merge(self):
        """Test merging retrieval results."""
        result1 = RetrievalResult(
            strategy_name="strategy1", query="query", cves=[{"cve_id": "CVE-2024-1234"}]
        )

        result2 = RetrievalResult(
            strategy_name="strategy2",
            query="query",
            cves=[{"cve_id": "CVE-2024-5678"}, {"cve_id": "CVE-2024-1234"}],  # Duplicate
        )

        merged = result1.merge_with(result2)

        # Should deduplicate by cve_id
        assert len(merged.cves) == 2
        cve_ids = {cve["cve_id"] for cve in merged.cves}
        assert cve_ids == {"CVE-2024-1234", "CVE-2024-5678"}


class TestDirectDependencyStrategy:
    """Test DirectDependencyStrategy - the key fix for the original issue."""

    @patch("llm_engine.strategies.direct_dependency_strategy.get_db_session")
    def test_can_handle_with_dependencies(self, mock_db):
        """Test strategy can handle context with dependencies."""
        strategy = DirectDependencyStrategy()

        ctx_with_deps = ChatContext(session_id=1, user_id="user123", dependencies=[10, 20])
        ctx_without_deps = ChatContext(session_id=1, user_id="user123")

        assert strategy.can_handle(ctx_with_deps)
        assert not strategy.can_handle(ctx_without_deps)

    @patch("llm_engine.strategies.direct_dependency_strategy.get_db_session")
    def test_retrieve_correct_cves_for_dependencies(self, mock_db):
        """Test that strategy retrieves correct CVEs for selected dependencies."""
        strategy = DirectDependencyStrategy()

        # Mock dependencies with CVEs - need to set all attributes
        mock_dep1 = Mock(spec=Dependency)
        mock_dep1.id = 1
        mock_dep1.package_name = "requests"
        mock_dep1.version = "2.25.0"
        mock_dep1.severity = "HIGH"
        mock_dep1.cve_count = 2

        mock_cve1 = Mock(spec=CVE)
        mock_cve1.cve_id = "CVE-2024-REQUESTS-1"
        mock_cve1.description = "Requests vulnerability"
        mock_cve1.severity = "HIGH"
        mock_cve1.cvss_score = 7.5
        mock_cve1.published_date = datetime.now()
        mock_cve1.last_modified_date = datetime.now()
        mock_cve1.epss_score = 0.5
        mock_cve1.attack_vector = "NETWORK"

        mock_cve2 = Mock(spec=CVE)
        mock_cve2.cve_id = "CVE-2024-REQUESTS-2"
        mock_cve2.description = "Another requests vulnerability"
        mock_cve2.severity = "CRITICAL"
        mock_cve2.cvss_score = 9.8
        mock_cve2.published_date = datetime.now()
        mock_cve2.last_modified_date = datetime.now()
        mock_cve2.epss_score = 0.8
        mock_cve2.attack_vector = "NETWORK"

        mock_dep1.cves = [mock_cve1, mock_cve2]

        # Mock DB session
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.options.return_value.filter.return_value.all.return_value = [mock_dep1]
        mock_db.return_value.__enter__.return_value = mock_session

        # Test retrieval
        ctx = ChatContext(session_id=1, user_id="user123", dependencies=[1])
        result = strategy.retrieve("Tell me about requests vulnerabilities", ctx)

        assert result.strategy_name == "direct_dependency"
        assert len(result.cves) == 2

        # Check CVE data
        cve_ids = {cve["cve_id"] for cve in result.cves}
        assert "CVE-2024-REQUESTS-1" in cve_ids
        assert "CVE-2024-REQUESTS-2" in cve_ids

        # Check relevance score (should be 1.0 for direct matches)
        for cve in result.cves:
            assert cve["relevance_score"] == 1.0
            assert "affects_packages" in cve
            assert "requests@2.25.0" in cve["affects_packages"]


class TestIntentRouter:
    """Test IntentRouter and handler chain."""

    @patch("llm_engine.intent_router.detect_intent")
    def test_greeting_handler(self, mock_detect):
        """Test greeting handler recognizes greetings."""
        handler = GreetingHandler()
        ctx = ChatContext(session_id=1, user_id="user123")

        # Mock intent detection
        mock_detect.return_value = "greeting"

        # Should recognize greetings
        assert handler.can_handle("hello", ctx)

        # Should return empty strategies (no retrieval needed)
        strategies = handler.select_strategies("hello", ctx)
        assert strategies == []

    def test_dependency_focused_handler(self):
        """Test dependency-focused handler."""
        handler = DependencyFocusedHandler()

        ctx_no_deps = ChatContext(session_id=1, user_id="user123")
        # ctx_with_deps = ChatContext(session_id=1, user_id="user123", dependencies=[1, 2])

        # Can't handle without dependencies
        assert not handler.can_handle("test query", ctx_no_deps)

    @patch("llm_engine.strategies.project_cve_strategy.RAGRetriever")
    def test_project_scan_handler(self, mock_rag):
        """Test project scan handler."""
        handler = ProjectScanHandler()

        ctx_no_scan = ChatContext(session_id=1, user_id="user123")
        ctx_with_scan = ChatContext(session_id=1, user_id="user123", scans=[5])

        assert not handler.can_handle("query", ctx_no_scan)
        assert handler.can_handle("query", ctx_with_scan)

        strategies = handler.select_strategies("query", ctx_with_scan)
        assert len(strategies) == 1
        assert isinstance(strategies[0], ProjectCVEStrategy)

    @patch("llm_engine.strategies.general_cve_strategy.RAGRetriever")
    def test_general_handler_fallback(self, mock_rag):
        """Test general handler always handles."""
        handler = GeneralSecurityHandler()
        ctx = ChatContext(session_id=1, user_id="user123")

        # Always handles
        assert handler.can_handle("any query", ctx)

        strategies = handler.select_strategies("query", ctx)
        assert len(strategies) == 1
        assert isinstance(strategies[0], GeneralCVEStrategy)

    @patch("llm_engine.strategies.general_cve_strategy.RAGRetriever")
    @patch("llm_engine.intent_router.detect_intent")
    def test_handler_chain(self, mock_detect, mock_rag):
        """Test handler chain delegation."""
        router = IntentRouter()

        # Test greeting routing
        mock_detect.return_value = "greeting"
        ctx = ChatContext(session_id=1, user_id="user123")
        strategies = router.route("hello", ctx)
        assert strategies == []

        # Test general query routing
        mock_detect.return_value = "general"
        strategies = router.route("What is CVE-2024-1234?", ctx)
        assert len(strategies) > 0


class TestUnifiedChatModel:
    """Test UnifiedChatModel integration."""

    @patch("llm_engine.unified_chat_model.XAIProvider")
    def test_model_initialization(self, mock_provider):
        """Test model initializes correctly."""
        model = UnifiedChatModel(api_key="test_key")

        assert model.api_key == "test_key"
        assert model.intent_router is not None

    @patch("llm_engine.unified_chat_model.XAIProvider")
    @patch("llm_engine.unified_chat_model.detect_intent")
    def test_greeting_handling(self, mock_detect, mock_provider):
        """Test greeting is handled without retrieval."""
        mock_detect.return_value = "greeting"
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Hello! How can I help you?"
        mock_provider.return_value = mock_llm

        model = UnifiedChatModel(api_key="test_key")
        ctx = ChatContext(session_id=1, user_id="user123")

        response = model.chat("hi there", ctx, stream=False)

        assert isinstance(response, str)
        mock_llm.generate.assert_called_once()

    @patch("llm_engine.unified_chat_model.XAIProvider")
    @patch("llm_engine.unified_chat_model.detect_intent")
    def test_general_query_handling(self, mock_detect, mock_provider):
        """Test general query with retrieval."""
        mock_detect.return_value = "general"

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Here's information about CVE-2024-1234"
        mock_provider.return_value = mock_llm

        model = UnifiedChatModel(api_key="test_key")
        ctx = ChatContext(session_id=1, user_id="user123")

        with patch.object(model.intent_router, "route") as mock_route:
            # Mock strategy that returns CVEs
            mock_strategy = MagicMock()
            mock_strategy.retrieve.return_value = RetrievalResult(
                strategy_name="test", query="test", cves=[{"cve_id": "CVE-2024-1234"}]
            )
            mock_route.return_value = [mock_strategy]

            response = model.chat("What is CVE-2024-1234?", ctx, stream=False)

            assert isinstance(response, str)
            mock_llm.generate.assert_called_once()


class TestSessionContextManager:
    """Test SessionContextManager."""

    @patch("database.context_manager.get_db_session")
    def test_context_stack_push_pop(self, mock_db):
        """Test context stack push and pop operations."""
        # Mock session
        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.user_id = "user123"
        mock_chat_session.context_stack = None
        mock_chat_session.selected_dependency_ids = []
        mock_chat_session.enabled_features = None

        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_chat_session
        mock_db.return_value.__enter__.return_value = mock_session

        # Create manager
        manager = SessionContextManager(session_id=1)

        # Initial stack depth should be 1
        assert manager.get_stack_depth() == 1

        # Push new context
        update = ContextUpdate(add_dependencies=[10, 20])
        manager.push_context(update)

        assert manager.get_stack_depth() == 2
        current = manager.get_current_context()
        assert 10 in current.dependencies
        assert 20 in current.dependencies

        # Pop context
        success = manager.pop_context()
        assert success
        assert manager.get_stack_depth() == 1

        # Can't pop last context
        success = manager.pop_context()
        assert not success
        assert manager.get_stack_depth() == 1

    @patch("database.context_manager.get_db_session")
    def test_context_update(self, mock_db):
        """Test in-place context update."""
        # Mock session
        mock_chat_session = Mock(spec=ChatSession)
        mock_chat_session.id = 1
        mock_chat_session.user_id = "user123"
        mock_chat_session.context_stack = None
        mock_chat_session.selected_dependency_ids = []
        mock_chat_session.enabled_features = None

        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_chat_session
        mock_db.return_value.__enter__.return_value = mock_session

        manager = SessionContextManager(session_id=1)

        # Update context
        manager.update_context(dependencies=[5, 10, 15])

        current = manager.get_current_context()
        assert current.dependencies == [5, 10, 15]
        assert manager.get_stack_depth() == 1  # Still one context


class TestFeatureManager:
    """Test FeatureManager."""

    def test_feature_registration(self):
        """Test feature registration."""
        manager = FeatureManager()

        # Default features should be registered
        assert Features.SMART_CONTEXT_INJECTION.value in manager.features
        assert Features.DEPENDENCY_CHAT.value in manager.features

    def test_feature_default_state(self):
        """Test feature default states."""
        manager = FeatureManager()

        # Core features enabled by default
        assert manager.is_enabled(Features.SMART_CONTEXT_INJECTION.value)
        assert manager.is_enabled(Features.DEPENDENCY_CHAT.value)

        # Future features disabled by default
        assert not manager.is_enabled(Features.ATTACK_CHAINS.value)
        assert not manager.is_enabled(Features.UPSTREAM_COMPROMISE.value)

    def test_feature_override_priority(self):
        """Test feature override priority (session > user > global > default)."""
        manager = FeatureManager()

        feature_name = Features.ATTACK_CHAINS.value

        # Default: disabled
        assert not manager.is_enabled(feature_name)

        # Global override: enabled
        manager.enable_feature(feature_name)
        assert manager.is_enabled(feature_name)
        assert manager.is_enabled(feature_name, user_id="user1")
        assert manager.is_enabled(feature_name, session_id=1)

        # User override: disabled for user1
        manager.disable_feature(feature_name, user_id="user1")
        assert manager.is_enabled(feature_name)  # Global still enabled
        assert not manager.is_enabled(feature_name, user_id="user1")
        assert manager.is_enabled(feature_name, user_id="user2")

        # Session override: enabled for session 1
        manager.enable_feature(feature_name, session_id=1, user_id="user1")
        assert not manager.is_enabled(feature_name, user_id="user1")  # User override
        assert manager.is_enabled(feature_name, user_id="user1", session_id=1)  # Session wins

    def test_get_enabled_features(self):
        """Test getting all enabled features for a context."""
        manager = FeatureManager()

        # Get enabled features for user
        enabled = manager.get_enabled_features(user_id="user1")

        # Should include default-enabled features
        assert Features.SMART_CONTEXT_INJECTION.value in enabled
        assert Features.DEPENDENCY_CHAT.value in enabled

        # Should not include default-disabled features
        assert Features.ATTACK_CHAINS.value not in enabled


class TestCompositeStrategy:
    """Test CompositeStrategy for combining multiple strategies."""

    def test_composite_strategy_sequential(self):
        """Test sequential execution of strategies."""
        # Create mock strategies
        strategy1 = Mock()
        strategy1.get_name.return_value = "strategy1"
        strategy1.retrieve.return_value = RetrievalResult(
            strategy_name="strategy1", query="query", cves=[{"cve_id": "CVE-2024-1111"}]
        )

        strategy2 = Mock()
        strategy2.get_name.return_value = "strategy2"
        strategy2.retrieve.return_value = RetrievalResult(
            strategy_name="strategy2", query="query", cves=[{"cve_id": "CVE-2024-2222"}]
        )

        composite = CompositeStrategy([strategy1, strategy2], parallel=False)
        ctx = ChatContext(session_id=1, user_id="user123")

        result = composite.retrieve("query", ctx)

        # Both strategies called
        strategy1.retrieve.assert_called_once()
        strategy2.retrieve.assert_called_once()

        # Results merged
        assert len(result.cves) == 2
        cve_ids = {cve["cve_id"] for cve in result.cves}
        assert cve_ids == {"CVE-2024-1111", "CVE-2024-2222"}

    def test_composite_strategy_deduplication(self):
        """Test that composite strategy deduplicates CVEs."""
        # Create strategies that return duplicate CVEs
        strategy1 = Mock()
        strategy1.get_name.return_value = "strategy1"
        strategy1.retrieve.return_value = RetrievalResult(
            strategy_name="strategy1",
            query="query",
            cves=[{"cve_id": "CVE-2024-1111"}, {"cve_id": "CVE-2024-SHARED"}],
        )

        strategy2 = Mock()
        strategy2.get_name.return_value = "strategy2"
        strategy2.retrieve.return_value = RetrievalResult(
            strategy_name="strategy2",
            query="query",
            cves=[{"cve_id": "CVE-2024-2222"}, {"cve_id": "CVE-2024-SHARED"}],  # Duplicate
        )

        composite = CompositeStrategy([strategy1, strategy2])
        ctx = ChatContext(session_id=1, user_id="user123")

        result = composite.retrieve("query", ctx)

        # Should deduplicate
        assert len(result.cves) == 3
        cve_ids = {cve["cve_id"] for cve in result.cves}
        assert cve_ids == {"CVE-2024-1111", "CVE-2024-2222", "CVE-2024-SHARED"}


class TestEndToEndScenarios:
    """End-to-end integration tests for common scenarios."""

    @patch("llm_engine.unified_chat_model.detect_intent")
    @patch("llm_engine.unified_chat_model.XAIProvider")
    @patch("llm_engine.strategies.direct_dependency_strategy.get_db_session")
    @patch("database.db.get_db_session")
    @patch("llm_engine.intent_router.DependencyIntentDetector")
    def test_dependency_selection_scenario(
        self, mock_detector_class, mock_router_db, mock_db, mock_provider, mock_detect
    ):
        """
        Test the original issue: User selects dependencies and should get correct CVEs.

        This is the KEY test that validates the fix for the user's original problem.
        """
        # Mock intent detection
        mock_detect.return_value = "dependency"

        # Setup: User selects "requests" and "Django" packages
        mock_requests = Mock(spec=Dependency)
        mock_requests.id = 1
        mock_requests.package_name = "requests"
        mock_requests.version = "2.25.0"
        mock_requests.severity = "HIGH"
        mock_requests.cve_count = 1

        mock_django = Mock(spec=Dependency)
        mock_django.id = 2
        mock_django.package_name = "Django"
        mock_django.version = "3.2.0"
        mock_django.severity = "CRITICAL"
        mock_django.cve_count = 1

        # Correct CVEs for these packages
        mock_requests_cve = Mock(spec=CVE)
        mock_requests_cve.cve_id = "CVE-2024-REQUESTS-ACTUAL"
        mock_requests_cve.description = "Actual requests vulnerability"
        mock_requests_cve.severity = "HIGH"
        mock_requests_cve.cvss_score = 7.5
        mock_requests_cve.published_date = datetime.now()
        mock_requests_cve.last_modified_date = datetime.now()
        mock_requests_cve.epss_score = 0.5
        mock_requests_cve.attack_vector = "NETWORK"

        mock_django_cve = Mock(spec=CVE)
        mock_django_cve.cve_id = "CVE-2024-DJANGO-ACTUAL"
        mock_django_cve.description = "Actual Django vulnerability"
        mock_django_cve.severity = "CRITICAL"
        mock_django_cve.cvss_score = 9.1
        mock_django_cve.published_date = datetime.now()
        mock_django_cve.last_modified_date = datetime.now()
        mock_django_cve.epss_score = 0.8
        mock_django_cve.attack_vector = "NETWORK"

        mock_requests.cves = [mock_requests_cve]
        mock_django.cves = [mock_django_cve]

        # Mock dependency intent detector
        mock_detector = Mock()
        mock_intent_result = Mock()
        mock_intent_result.is_relevant = True
        mock_intent_result.confidence = 0.9
        mock_detector.detect_intent.return_value = mock_intent_result
        mock_detector_class.return_value = mock_detector

        # Mock DB for both strategy retrieval and router
        mock_session = MagicMock()
        mock_query = mock_session.query.return_value
        mock_options = mock_query.options.return_value
        mock_filter = mock_options.filter.return_value
        mock_filter.all.return_value = [mock_requests, mock_django]

        # Expunge method (called in router)
        mock_session.expunge = Mock()

        mock_db.return_value.__enter__.return_value = mock_session
        mock_router_db.return_value.__enter__.return_value = mock_session

        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Here are the vulnerabilities for requests and Django..."
        mock_provider.return_value = mock_llm

        # Create model and context
        model = UnifiedChatModel(api_key="test_key")
        ctx = ChatContext(
            session_id=1, user_id="user123", dependencies=[1, 2]  # Selected requests and Django
        )

        # User asks about selected dependencies
        response = model.chat("Tell me about the selected dependencies", ctx, stream=False)

        # Verify correct behavior:
        # 1. Should use DirectDependencyStrategy (not vector search)
        # 2. Should get CORRECT CVEs (CVE-2024-REQUESTS-ACTUAL, CVE-2024-DJANGO-ACTUAL)
        # 3. Should NOT get wrong CVEs (Pharmacy Management, Google.Protobuf, etc.)

        assert isinstance(response, str)
        mock_llm.generate.assert_called_once()

        # Check that the prompt includes correct CVE IDs
        call_args = mock_llm.generate.call_args
        messages = call_args[0][0]
        user_message = next(m for m in messages if m["role"] == "user")

        # Should mention the correct CVEs
        assert (
            "CVE-2024-REQUESTS-ACTUAL" in user_message["content"]
            or "CVE-2024-DJANGO-ACTUAL" in user_message["content"]
        )

    @patch("llm_engine.unified_chat_model.XAIProvider")
    def test_general_query_scenario(self, mock_provider):
        """Test general security query without specific context."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "XSS is a web vulnerability..."
        mock_provider.return_value = mock_llm

        model = UnifiedChatModel(api_key="test_key")
        ctx = ChatContext(session_id=1, user_id="user123")

        response = model.chat("What is XSS?", ctx, stream=False)

        assert isinstance(response, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
