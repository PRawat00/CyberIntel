"""
Feature Manager for enabling/disabling chat features.

Provides a centralized system for feature flags with per-user and per-session
overrides.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class FeatureFlag:
    """
    Represents a toggleable feature.

    Supports global defaults with per-user and per-session overrides.
    """

    def __init__(self, name: str, enabled_by_default: bool = False, description: str = ""):
        """
        Initialize feature flag.

        Args:
            name: Feature name
            enabled_by_default: Default state
            description: Human-readable description
        """
        self.name = name
        self.enabled_by_default = enabled_by_default
        self.description = description
        self.global_override: bool | None = None
        self.user_overrides: dict[str, bool] = {}
        self.session_overrides: dict[int, bool] = {}

    def is_enabled(self, user_id: str | None = None, session_id: int | None = None) -> bool:
        """
        Check if feature is enabled.

        Priority (highest to lowest):
        1. Session-specific override
        2. User-specific override
        3. Global override
        4. Default value

        Args:
            user_id: User ID to check
            session_id: Session ID to check

        Returns:
            True if feature is enabled
        """
        # Check session override
        if session_id is not None and session_id in self.session_overrides:
            return self.session_overrides[session_id]

        # Check user override
        if user_id is not None and user_id in self.user_overrides:
            return self.user_overrides[user_id]

        # Check global override
        if self.global_override is not None:
            return self.global_override

        # Fall back to default
        return self.enabled_by_default

    def set_global(self, enabled: bool):
        """Set global override."""
        self.global_override = enabled
        logger.info(f"Feature '{self.name}' globally set to {enabled}")

    def set_for_user(self, user_id: str, enabled: bool):
        """Set override for specific user."""
        self.user_overrides[user_id] = enabled
        logger.info(f"Feature '{self.name}' set to {enabled} for user {user_id}")

    def set_for_session(self, session_id: int, enabled: bool):
        """Set override for specific session."""
        self.session_overrides[session_id] = enabled
        logger.info(f"Feature '{self.name}' set to {enabled} for session {session_id}")

    def clear_overrides(self, user_id: str | None = None, session_id: int | None = None):
        """Clear overrides."""
        if session_id is not None:
            self.session_overrides.pop(session_id, None)
        if user_id is not None:
            self.user_overrides.pop(user_id, None)


class Features(Enum):
    """
    Enum of all available features.

    This provides a centralized place to define all feature flags.
    """

    # Core features (currently enabled)
    SMART_CONTEXT_INJECTION = "smart_context_injection"
    DEPENDENCY_CHAT = "dependency_chat"
    PROJECT_SCAN_ANALYSIS = "project_scan_analysis"

    # Future features (disabled by default)
    ATTACK_CHAINS = "attack_chains"
    UPSTREAM_COMPROMISE = "upstream_compromise"
    VULNERABILITY_LIFECYCLE = "vulnerability_lifecycle"
    REMEDIATION_TRACKING = "remediation_tracking"
    MULTI_SCAN_COMPARISON = "multi_scan_comparison"
    CUSTOM_CONTEXT = "custom_context"
    TEAM_COLLABORATION = "team_collaboration"


class FeatureManager:
    """
    Centralized feature flag management.

    Singleton that manages all feature flags in the system.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.features: dict[str, FeatureFlag] = {}
        self._register_default_features()
        self._initialized = True
        logger.info("FeatureManager initialized")

    def _register_default_features(self):
        """Register all default features."""
        # Core features (enabled)
        self.register(
            Features.SMART_CONTEXT_INJECTION.value,
            enabled_by_default=True,
            description="Smart intent-based context injection",
        )
        self.register(
            Features.DEPENDENCY_CHAT.value,
            enabled_by_default=True,
            description="Chat about selected dependencies",
        )
        self.register(
            Features.PROJECT_SCAN_ANALYSIS.value,
            enabled_by_default=True,
            description="Analyze project scans",
        )

        # Future features (disabled)
        self.register(
            Features.ATTACK_CHAINS.value,
            enabled_by_default=False,
            description="Attack chain analysis and visualization",
        )
        self.register(
            Features.UPSTREAM_COMPROMISE.value,
            enabled_by_default=False,
            description="Upstream dependency compromise detection",
        )
        self.register(
            Features.VULNERABILITY_LIFECYCLE.value,
            enabled_by_default=False,
            description="Vulnerability lifecycle tracking",
        )
        self.register(
            Features.REMEDIATION_TRACKING.value,
            enabled_by_default=False,
            description="Track remediation progress",
        )
        self.register(
            Features.MULTI_SCAN_COMPARISON.value,
            enabled_by_default=False,
            description="Compare multiple scans",
        )
        self.register(
            Features.CUSTOM_CONTEXT.value,
            enabled_by_default=False,
            description="Upload custom docs/configs for context",
        )
        self.register(
            Features.TEAM_COLLABORATION.value,
            enabled_by_default=False,
            description="Share sessions and collaborate",
        )

    def register(self, name: str, enabled_by_default: bool = False, description: str = ""):
        """
        Register a new feature flag.

        Args:
            name: Feature name
            enabled_by_default: Default state
            description: Description of feature
        """
        if name in self.features:
            logger.warning(f"Feature '{name}' already registered, overwriting")

        self.features[name] = FeatureFlag(name, enabled_by_default, description)
        logger.info(f"Registered feature: {name} (default: {enabled_by_default})")

    def is_enabled(
        self, feature_name: str, user_id: str | None = None, session_id: int | None = None
    ) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_name: Name of feature
            user_id: User ID to check
            session_id: Session ID to check

        Returns:
            True if feature is enabled
        """
        if feature_name not in self.features:
            logger.warning(f"Unknown feature: {feature_name}")
            return False

        return self.features[feature_name].is_enabled(user_id, session_id)

    def get_enabled_features(
        self, user_id: str | None = None, session_id: int | None = None
    ) -> set[str]:
        """
        Get set of all enabled features for context.

        Args:
            user_id: User ID
            session_id: Session ID

        Returns:
            Set of enabled feature names
        """
        return {
            name for name, flag in self.features.items() if flag.is_enabled(user_id, session_id)
        }

    def enable_feature(
        self, feature_name: str, user_id: str | None = None, session_id: int | None = None
    ):
        """
        Enable a feature.

        Args:
            feature_name: Name of feature
            user_id: User ID (for user-specific override)
            session_id: Session ID (for session-specific override)
        """
        if feature_name not in self.features:
            raise ValueError(f"Unknown feature: {feature_name}")

        feature = self.features[feature_name]

        if session_id is not None:
            feature.set_for_session(session_id, True)
        elif user_id is not None:
            feature.set_for_user(user_id, True)
        else:
            feature.set_global(True)

    def disable_feature(
        self, feature_name: str, user_id: str | None = None, session_id: int | None = None
    ):
        """
        Disable a feature.

        Args:
            feature_name: Name of feature
            user_id: User ID (for user-specific override)
            session_id: Session ID (for session-specific override)
        """
        if feature_name not in self.features:
            raise ValueError(f"Unknown feature: {feature_name}")

        feature = self.features[feature_name]

        if session_id is not None:
            feature.set_for_session(session_id, False)
        elif user_id is not None:
            feature.set_for_user(user_id, False)
        else:
            feature.set_global(False)

    def get_all_features(self) -> dict[str, FeatureFlag]:
        """Get all registered features."""
        return self.features.copy()


# Global instance
_feature_manager = FeatureManager()


def get_feature_manager() -> FeatureManager:
    """Get the global feature manager instance."""
    return _feature_manager
