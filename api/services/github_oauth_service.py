"""GitHub OAuth service for handling OAuth flow.

This module provides functionality to:
- Generate OAuth authorization URLs
- Exchange authorization codes for access tokens
- Get GitHub user information after OAuth
"""

import logging
import os
import secrets
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    """Service for handling GitHub OAuth flow."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105
    API_URL = "https://api.github.com"

    # Required scopes for the application
    SCOPES = ["repo", "read:user", "user:email"]

    def __init__(self):
        """Initialize OAuth service with credentials from environment."""
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.callback_url = os.getenv(
            "GITHUB_OAUTH_CALLBACK_URL", "http://localhost:3000/auth/github/callback"
        )

        if not self.client_id or not self.client_secret:
            logger.warning(
                "GitHub OAuth credentials not configured. "
                "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
            )

    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)

    def generate_state(self) -> str:
        """Generate a secure random state parameter for CSRF protection.

        Returns:
            A secure random string
        """
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str) -> str:
        """Generate the GitHub OAuth authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            Full authorization URL to redirect user to
        """
        if not self.is_configured():
            raise ValueError("GitHub OAuth is not configured")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": " ".join(self.SCOPES),
            "state": state,
        }

        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange an authorization code for an access token.

        Args:
            code: The authorization code from GitHub callback

        Returns:
            Dictionary containing access_token and related fields

        Raises:
            Exception: If the exchange fails
        """
        if not self.is_configured():
            raise ValueError("GitHub OAuth is not configured")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }

        headers = {
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.TOKEN_URL,
                data=data,
                headers=headers,
            ) as response:
                result = await response.json()

                if "error" in result:
                    error_desc = result.get("error_description", result.get("error"))
                    logger.error(f"GitHub OAuth error: {error_desc}")
                    raise Exception(f"GitHub OAuth failed: {error_desc}")

                return {
                    "access_token": result.get("access_token"),
                    "token_type": result.get("token_type"),
                    "scope": result.get("scope"),
                    "refresh_token": result.get("refresh_token"),
                }

    async def get_github_user(self, access_token: str) -> dict:
        """Get the authenticated GitHub user's information.

        Args:
            access_token: The OAuth access token

        Returns:
            Dictionary containing user information

        Raises:
            Exception: If the API call fails
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with aiohttp.ClientSession() as session:
            # Get user info
            async with session.get(
                f"{self.API_URL}/user",
                headers=headers,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Failed to get GitHub user: {error}")

                user_data = await response.json()

            # Get user's primary email if not public
            email = user_data.get("email")
            if not email:
                async with session.get(
                    f"{self.API_URL}/user/emails",
                    headers=headers,
                ) as email_response:
                    if email_response.status == 200:
                        emails = await email_response.json()
                        # Find primary email
                        for e in emails:
                            if e.get("primary") and e.get("verified"):
                                email = e.get("email")
                                break

            return {
                "id": user_data.get("id"),
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "email": email,
                "avatar_url": user_data.get("avatar_url"),
                "html_url": user_data.get("html_url"),
            }

    async def revoke_token(self, access_token: str) -> bool:
        """Revoke an OAuth access token.

        Note: GitHub OAuth apps can't revoke tokens programmatically.
        Users must revoke via GitHub settings. This is a placeholder.

        Args:
            access_token: The token to revoke

        Returns:
            True (always, as we can't actually revoke)
        """
        # GitHub OAuth doesn't support programmatic token revocation
        # The user must revoke access via GitHub settings
        logger.info("Token revocation requested - user should revoke via GitHub settings")
        return True


# Singleton instance
_oauth_service = None


def get_github_oauth_service() -> GitHubOAuthService:
    """Get the singleton OAuth service instance.

    Returns:
        The GitHubOAuthService singleton
    """
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = GitHubOAuthService()
    return _oauth_service
