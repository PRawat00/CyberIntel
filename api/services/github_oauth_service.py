"""GitHub App OAuth service for handling OAuth flow with fine-grained permissions.

This module provides functionality to:
- Redirect users to GitHub App installation page (where they select repos)
- Exchange authorization codes for access tokens
- Generate installation access tokens using JWT
- List repositories from specific installations (fine-grained access)
"""

import logging
import os
import secrets
import time
from urllib.parse import urlencode

import aiohttp
import jwt

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    """Service for handling GitHub App OAuth flow with fine-grained repo access."""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105
    API_URL = "https://api.github.com"

    def __init__(self):
        """Initialize OAuth service with GitHub App credentials from environment."""
        # GitHub App credentials (use _APP suffix to distinguish from legacy OAuth App)
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")
        self.client_id = os.getenv("GITHUB_CLIENT_ID_APP")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET_APP")
        self.callback_url = os.getenv(
            "GITHUB_OAUTH_CALLBACK_URL", "http://localhost:3000/auth/github/callback"
        )

        if not self.client_id or not self.client_secret:
            logger.warning(
                "GitHub OAuth credentials not configured. "
                "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
            )

        if not self.app_id or not self.private_key:
            logger.warning(
                "GitHub App credentials not configured. "
                "Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY environment variables."
            )

    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)

    def is_app_configured(self) -> bool:
        """Check if GitHub App is properly configured for installation tokens."""
        return bool(self.app_id and self.private_key)

    def generate_state(self) -> str:
        """Generate a secure random state parameter for CSRF protection.

        Returns:
            A secure random string
        """
        return secrets.token_urlsafe(32)

    def get_installation_url(self) -> str:
        """Get the URL to install/configure the GitHub App.

        This is where users select which repos to grant access to.

        Returns:
            URL to GitHub App installation page
        """
        if not self.app_id:
            raise ValueError("GitHub App ID not configured")

        # GitHub App installation URL - users select repos here
        return "https://github.com/apps/repo_cyber_intel_prod/installations/new"

    def get_authorization_url(self, state: str, installation_id: int | None = None) -> str:
        """Generate the GitHub OAuth authorization URL.

        For GitHub Apps, users are redirected here after installation.
        The installation_id is passed through if available.

        Args:
            state: CSRF protection state parameter
            installation_id: Optional installation ID from GitHub App install

        Returns:
            Full authorization URL to redirect user to
        """
        if not self.is_configured():
            raise ValueError("GitHub OAuth is not configured")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.callback_url,
            "scope": "repo",  # Access to public and private repositories
            "state": state,
        }

        # If we have installation_id, include it in state for callback
        if installation_id:
            params["state"] = f"{state}:{installation_id}"

        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def _generate_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication.

        Returns:
            JWT token string

        Raises:
            ValueError: If App credentials not configured
        """
        if not self.is_app_configured():
            raise ValueError("GitHub App credentials not configured")

        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock drift)
            "exp": now + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id,
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_access_token(self, installation_id: int) -> dict:
        """Get an installation access token for accessing repos.

        This token is used to access repositories that the user has granted
        access to during installation.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            Dictionary with token and expiration

        Raises:
            Exception: If token generation fails
        """
        jwt_token = self._generate_jwt()

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.API_URL}/app/installations/{installation_id}/access_tokens",
                headers=headers,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    logger.error(f"Failed to get installation token: {error}")
                    raise Exception(f"Failed to get installation access token: {error}")

                data = await response.json()
                return {
                    "token": data.get("token"),
                    "expires_at": data.get("expires_at"),
                    "permissions": data.get("permissions", {}),
                    "repository_selection": data.get("repository_selection"),
                }

    async def get_user_installations(self, access_token: str) -> list[dict]:
        """Get all GitHub App installations for the authenticated user.

        Args:
            access_token: User's OAuth access token

        Returns:
            List of installations with their IDs and account info
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.API_URL}/user/installations",
                headers=headers,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"Failed to get user installations: {error}")
                    return []

                data = await response.json()
                installations = data.get("installations", [])

                return [
                    {
                        "id": inst.get("id"),
                        "account": {
                            "login": inst.get("account", {}).get("login"),
                            "avatar_url": inst.get("account", {}).get("avatar_url"),
                            "type": inst.get("account", {}).get("type"),
                        },
                        "repository_selection": inst.get("repository_selection"),
                        "permissions": inst.get("permissions", {}),
                    }
                    for inst in installations
                ]

    async def get_installation_repos(self, installation_id: int) -> list[dict]:
        """Get repositories accessible to a specific installation.

        This returns ONLY the repos the user selected during installation.

        Args:
            installation_id: The GitHub App installation ID

        Returns:
            List of repository info
        """
        try:
            token_data = await self.get_installation_access_token(installation_id)
            token = token_data["token"]
        except Exception as e:
            logger.error(f"Failed to get installation token: {e}")
            raise

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.API_URL}/installation/repositories",
                headers=headers,
                params={"per_page": 100},
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"Failed to get installation repos: {error}")
                    raise Exception(f"Failed to get installation repositories: {error}")

                data = await response.json()
                repos = data.get("repositories", [])

                return [
                    {
                        "id": repo.get("id"),
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "private": repo.get("private"),
                        "default_branch": repo.get("default_branch", "main"),
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "updated_at": repo.get("updated_at"),
                    }
                    for repo in repos
                ]

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
