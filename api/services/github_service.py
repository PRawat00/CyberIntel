"""GitHub API service for repository integration.

This module provides functionality to:
- Authenticate with GitHub using Personal Access Tokens
- List user repositories
- Fetch repository contents
- Detect and retrieve dependency files
"""

import base64
import logging
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    # Common dependency file patterns
    DEPENDENCY_FILES = {
        "npm": ["package.json", "package-lock.json", "yarn.lock"],
        "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "requirements.in"],
        "go": ["go.mod", "go.sum"],
        "ruby": ["Gemfile", "Gemfile.lock"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "rust": ["Cargo.toml", "Cargo.lock"],
        "php": ["composer.json", "composer.lock"],
        "dotnet": ["*.csproj", "*.fsproj", "*.vbproj", "packages.config"],
    }

    def __init__(self, token: str):
        """Initialize GitHub service with Personal Access Token.

        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        }
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST/PUT requests

        Returns:
            Response data as dictionary

        Raises:
            Exception: If the request fails
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.BASE_URL}{endpoint}"

        async with self.session.request(
            method,
            url,
            headers=self.headers,
            params=params,
            json=json_data,
        ) as response:
            if response.status == 401:
                raise Exception("Invalid or expired GitHub token")
            elif response.status == 403:
                # Check for rate limit
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    reset_time = response.headers.get("X-RateLimit-Reset")
                    if remaining == "0":
                        reset_dt = datetime.fromtimestamp(int(reset_time))
                        raise Exception(f"GitHub API rate limit exceeded. Resets at {reset_dt}")
                raise Exception("Forbidden: Insufficient permissions")
            elif response.status == 404:
                raise Exception("Resource not found")
            elif response.status >= 400:
                error_data = await response.json()
                raise Exception(f"GitHub API error: {error_data.get('message', 'Unknown error')}")

            return await response.json()

    async def test_connection(self) -> dict[str, Any]:
        """Test the GitHub token and connection.

        Returns:
            User information if successful
        """
        try:
            user_data = await self._make_request("GET", "/user")
            return {
                "success": True,
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "public_repos": user_data.get("public_repos"),
                "private_repos": user_data.get("total_private_repos", 0),
            }
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return {"success": False, "error": str(e)}

    async def list_repositories(
        self,
        type: str = "all",
        sort: str = "updated",
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """List repositories accessible to the authenticated user.

        Args:
            type: Type of repositories (all, owner, public, private, member)
            sort: Sort by (created, updated, pushed, full_name)
            per_page: Number of results per page (max 100)
            page: Page number

        Returns:
            List of repository data
        """
        params = {
            "type": type,
            "sort": sort,
            "per_page": per_page,
            "page": page,
        }

        repos = await self._make_request("GET", "/user/repos", params=params)

        # Extract relevant information
        return [
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "owner": repo["owner"]["login"],
                "description": repo.get("description"),
                "private": repo["private"],
                "html_url": repo["html_url"],
                "default_branch": repo.get("default_branch", "main"),
                "language": repo.get("language"),
                "updated_at": repo.get("updated_at"),
                "size": repo.get("size"),
            }
            for repo in repos
        ]

    async def get_repository_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get contents of a repository path.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path in repository (empty for root)
            ref: Branch, tag, or commit SHA (optional)

        Returns:
            List of file/directory information
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else None

        contents = await self._make_request("GET", endpoint, params=params)

        # Ensure we always return a list
        if isinstance(contents, dict):
            contents = [contents]

        return contents

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> str:
        """Get the content of a specific file.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            ref: Branch, tag, or commit SHA (optional)

        Returns:
            Decoded file content as string
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else None

        file_data = await self._make_request("GET", endpoint, params=params)

        if file_data.get("type") != "file":
            raise Exception(f"Path {path} is not a file")

        # Content is base64 encoded
        content = file_data.get("content", "")
        if content:
            # Remove newlines and decode
            content = content.replace("\n", "")
            decoded = base64.b64decode(content).decode("utf-8")
            return decoded

        # If no content, try download_url
        download_url = file_data.get("download_url")
        if download_url:
            async with self.session.get(download_url) as response:
                return await response.text()

        raise Exception(f"Could not retrieve content for {path}")

    async def find_dependency_files(
        self,
        owner: str,
        repo: str,
        ref: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find all dependency files in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch, tag, or commit SHA (optional)

        Returns:
            List of dependency file information with ecosystem type
        """
        dependency_files = []

        try:
            # Get root directory contents
            root_contents = await self.get_repository_contents(owner, repo, "", ref)

            for item in root_contents:
                if item["type"] == "file":
                    file_name = item["name"]

                    # Check against known dependency patterns
                    for ecosystem, patterns in self.DEPENDENCY_FILES.items():
                        if file_name in patterns:
                            dependency_files.append(
                                {
                                    "name": file_name,
                                    "path": item["path"],
                                    "ecosystem": ecosystem,
                                    "sha": item["sha"],
                                    "size": item["size"],
                                    "download_url": item.get("download_url"),
                                }
                            )
                            break

            # Also check common subdirectories
            subdirs_to_check = ["backend", "frontend", "server", "client", "api", "src"]

            for subdir in subdirs_to_check:
                try:
                    subdir_contents = await self.get_repository_contents(owner, repo, subdir, ref)
                    for item in subdir_contents:
                        if item["type"] == "file":
                            file_name = item["name"]

                            for ecosystem, patterns in self.DEPENDENCY_FILES.items():
                                if file_name in patterns:
                                    dependency_files.append(
                                        {
                                            "name": file_name,
                                            "path": item["path"],
                                            "ecosystem": ecosystem,
                                            "sha": item["sha"],
                                            "size": item["size"],
                                            "download_url": item.get("download_url"),
                                        }
                                    )
                                    break
                except Exception as e:
                    # Subdirectory might not exist, log and continue
                    logger.debug(f"Could not check subdirectory {subdir}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error finding dependency files: {e}")
            raise

        return dependency_files

    async def import_dependency_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Import a dependency file from GitHub.

        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to dependency file
            ref: Branch, tag, or commit SHA (optional)

        Returns:
            Dictionary with file content and metadata
        """
        try:
            # Get file content
            content = await self.get_file_content(owner, repo, file_path, ref)

            # Determine ecosystem based on file name
            file_name = file_path.split("/")[-1]
            ecosystem = "unknown"

            for eco, patterns in self.DEPENDENCY_FILES.items():
                if file_name in patterns:
                    ecosystem = eco
                    break

            return {
                "success": True,
                "content": content,
                "file_name": file_name,
                "file_path": file_path,
                "ecosystem": ecosystem,
                "github_repo": f"{owner}/{repo}",
                "github_branch": ref or "main",
                "source": "github",
            }

        except Exception as e:
            logger.error(f"Error importing file from GitHub: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_rate_limit(self) -> dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Rate limit information
        """
        rate_limit_data = await self._make_request("GET", "/rate_limit")
        core_limits = rate_limit_data.get("rate", {})

        return {
            "limit": core_limits.get("limit"),
            "remaining": core_limits.get("remaining"),
            "reset": datetime.fromtimestamp(core_limits.get("reset", 0)),
            "used": core_limits.get("used", 0),
        }


# Utility function for encrypting tokens
def encrypt_token(token: str, key: str) -> str:
    """Encrypt a GitHub token for storage.

    Args:
        token: The token to encrypt
        key: Encryption key

    Returns:
        Encrypted token as base64 string
    """
    # Simple XOR encryption (in production, use proper encryption like Fernet)
    # This is a placeholder - implement proper encryption
    import hashlib

    key_hash = hashlib.sha256(key.encode()).digest()
    encrypted = bytearray()

    for i, char in enumerate(token.encode()):
        encrypted.append(char ^ key_hash[i % len(key_hash)])

    return base64.b64encode(encrypted).decode()


def decrypt_token(encrypted: str, key: str) -> str:
    """Decrypt a GitHub token.

    Args:
        encrypted: Encrypted token as base64 string
        key: Encryption key

    Returns:
        Decrypted token
    """
    # Simple XOR decryption (in production, use proper encryption like Fernet)
    # This is a placeholder - implement proper encryption
    import hashlib

    key_hash = hashlib.sha256(key.encode()).digest()
    encrypted_bytes = base64.b64decode(encrypted)
    decrypted = bytearray()

    for i, byte in enumerate(encrypted_bytes):
        decrypted.append(byte ^ key_hash[i % len(key_hash)])

    return decrypted.decode()
