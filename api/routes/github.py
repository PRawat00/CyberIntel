"""GitHub App integration API routes with fine-grained repo access."""

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.middleware.auth import RequireAuth, User
from api.services.github_oauth_service import get_github_oauth_service
from api.services.github_service import GitHubService, decrypt_token, encrypt_token
from api.services.github_sync_service import get_github_sync_service
from database.db import get_db_session
from database.models import GitHubConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/github",
    tags=["github"],
)

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY", "default-dev-key-change-in-prod")


# Pydantic models for request/response
class InstallResponse(BaseModel):
    """Response for GitHub App installation URL."""

    url: str


class OAuthAuthorizeResponse(BaseModel):
    """Response for OAuth authorize endpoint."""

    url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Request for OAuth callback."""

    code: str = Field(..., description="Authorization code from GitHub")
    state: str = Field(..., description="State parameter for CSRF protection")
    installation_id: int | None = Field(None, description="GitHub App installation ID")


class OAuthCallbackResponse(BaseModel):
    """Response for OAuth callback."""

    success: bool
    message: str
    github_username: str | None = None
    installation_id: int | None = None


class GitHubConnectionResponse(BaseModel):
    """Response for connection status."""

    id: int | None = None
    installation_id: int | None = None
    github_username: str | None = None
    github_avatar_url: str | None = None
    is_active: bool = False
    auto_sync_enabled: bool = True
    last_sync_at: str | None = None
    repo_full_name: str | None = None
    sync_error: str | None = None


class SetRepoRequest(BaseModel):
    """Request for setting which repo to track."""

    repo_full_name: str = Field(..., description="Repository in 'owner/repo' format")


class SetRepoResponse(BaseModel):
    """Response for setting repo."""

    success: bool
    message: str
    repo_full_name: str | None = None


class SyncResponse(BaseModel):
    """Response for sync operation."""

    success: bool
    message: str | None = None
    error: str | None = None
    files_found: int = 0
    scans_created: int = 0


class RepoOption(BaseModel):
    """Repository option for selection dropdown."""

    full_name: str
    name: str
    is_private: bool
    default_branch: str
    description: str | None = None


class RepoListResponse(BaseModel):
    """Response for listing repos."""

    success: bool
    repositories: list[RepoOption]


# OAuth state storage (in production, use Redis or database)
_oauth_states: dict[str, str] = {}


@router.get("/install", response_model=InstallResponse)
async def get_install_url(user: User = RequireAuth):
    """Get GitHub App installation URL.

    Returns the URL to redirect user to for GitHub App installation.
    Users will select which repositories to grant access to on this page.
    """
    oauth_service = get_github_oauth_service()

    if not oauth_service.is_app_configured():
        raise HTTPException(
            status_code=503,
            detail="GitHub App is not configured. Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY.",
        )

    return InstallResponse(url=oauth_service.get_installation_url())


@router.get("/oauth/authorize", response_model=OAuthAuthorizeResponse)
async def get_oauth_authorize_url(user: User = RequireAuth):
    """Get GitHub OAuth authorization URL.

    Returns the URL to redirect the user to for GitHub OAuth authorization.
    This is typically called after the user has installed the GitHub App.
    """
    oauth_service = get_github_oauth_service()

    if not oauth_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
        )

    # Generate state for CSRF protection
    state = oauth_service.generate_state()

    # Store state with user ID (in production, use Redis with TTL)
    _oauth_states[state] = user.id

    # Get authorization URL
    url = oauth_service.get_authorization_url(state)

    return OAuthAuthorizeResponse(url=url, state=state)


@router.post("/oauth/callback", response_model=OAuthCallbackResponse)
async def handle_oauth_callback(request: OAuthCallbackRequest, user: User = RequireAuth):
    """Handle GitHub OAuth callback.

    Exchanges the authorization code for an access token and saves the connection.
    If installation_id is provided (from GitHub App install), it's stored for fine-grained access.
    """
    # Extract state and optional installation_id from state parameter
    state_parts = request.state.split(":")
    state = state_parts[0]
    installation_id = request.installation_id
    if len(state_parts) > 1 and not installation_id:
        try:
            installation_id = int(state_parts[1])
        except ValueError:
            pass

    # Verify state
    stored_user_id = _oauth_states.get(state)
    if not stored_user_id or stored_user_id != user.id:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter. Please try connecting again.",
        )

    # Remove used state
    del _oauth_states[state]

    oauth_service = get_github_oauth_service()

    try:
        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token(request.code)
        access_token = token_data["access_token"]

        # Get GitHub user info
        github_user = await oauth_service.get_github_user(access_token)

        # If no installation_id provided, try to get from user's installations
        if not installation_id:
            installations = await oauth_service.get_user_installations(access_token)
            if installations:
                # Use the first installation (usually the most recent)
                installation_id = installations[0]["id"]

        # Encrypt token for storage
        encrypted_token = encrypt_token(access_token, ENCRYPTION_KEY)

        with get_db_session() as session:
            # Check if connection already exists
            existing = (
                session.query(GitHubConnection).filter(GitHubConnection.user_id == user.id).first()
            )

            if existing:
                # Update existing connection
                existing.access_token = encrypted_token
                existing.installation_id = installation_id
                existing.github_user_id = github_user["id"]
                existing.github_username = github_user["login"]
                existing.github_avatar_url = github_user.get("avatar_url")
                existing.is_active = 1
                existing.sync_error = None
            else:
                # Create new connection
                connection = GitHubConnection(
                    user_id=user.id,
                    access_token=encrypted_token,
                    installation_id=installation_id,
                    github_user_id=github_user["id"],
                    github_username=github_user["login"],
                    github_avatar_url=github_user.get("avatar_url"),
                    is_active=1,
                    auto_sync_enabled=1,
                )
                session.add(connection)

            session.commit()

        return OAuthCallbackResponse(
            success=True,
            message="GitHub connected successfully",
            github_username=github_user["login"],
            installation_id=installation_id,
        )

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connection", response_model=GitHubConnectionResponse)
async def get_connection_status(user: User = RequireAuth):
    """Get the current GitHub connection status."""
    with get_db_session() as session:
        connection = (
            session.query(GitHubConnection).filter(GitHubConnection.user_id == user.id).first()
        )

        if not connection:
            return GitHubConnectionResponse(is_active=False)

        return GitHubConnectionResponse(
            id=connection.id,
            installation_id=connection.installation_id,
            github_username=connection.github_username,
            github_avatar_url=connection.github_avatar_url,
            is_active=bool(connection.is_active),
            auto_sync_enabled=bool(connection.auto_sync_enabled),
            last_sync_at=connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            repo_full_name=connection.repo_full_name,
            sync_error=connection.sync_error,
        )


@router.delete("/connection")
async def disconnect_github(user: User = RequireAuth):
    """Disconnect GitHub integration."""
    with get_db_session() as session:
        connection = (
            session.query(GitHubConnection).filter(GitHubConnection.user_id == user.id).first()
        )

        if not connection:
            return {"success": False, "message": "No GitHub connection found"}

        session.delete(connection)
        session.commit()

        return {"success": True, "message": "GitHub disconnected successfully"}


@router.get("/repos", response_model=RepoListResponse)
async def list_repositories(user: User = RequireAuth):
    """List repositories accessible to the GitHub App installation.

    Returns ONLY the repositories the user selected during GitHub App installation.
    This provides fine-grained access control.
    """
    with get_db_session() as session:
        connection = (
            session.query(GitHubConnection)
            .filter(GitHubConnection.user_id == user.id)
            .filter(GitHubConnection.is_active == 1)
            .first()
        )

        if not connection:
            raise HTTPException(
                status_code=401,
                detail="No active GitHub connection. Please connect GitHub first.",
            )

        oauth_service = get_github_oauth_service()

        try:
            # Try to use GitHub App installation for fine-grained access
            if connection.installation_id and oauth_service.is_app_configured():
                repos = await oauth_service.get_installation_repos(connection.installation_id)
                return RepoListResponse(
                    success=True,
                    repositories=[
                        RepoOption(
                            full_name=repo["full_name"],
                            name=repo["name"],
                            is_private=repo["private"],
                            default_branch=repo["default_branch"],
                            description=repo.get("description"),
                        )
                        for repo in repos
                    ],
                )

            # Fallback to OAuth token (lists all repos user has access to)
            access_token = decrypt_token(connection.access_token, ENCRYPTION_KEY)

            async with GitHubService(access_token) as github:
                repos = await github.list_repositories(
                    type="all",
                    sort="updated",
                    per_page=100,
                )

            return RepoListResponse(
                success=True,
                repositories=[
                    RepoOption(
                        full_name=repo["full_name"],
                        name=repo["name"],
                        is_private=repo["private"],
                        default_branch=repo["default_branch"],
                        description=repo.get("description"),
                    )
                    for repo in repos
                ],
            )

        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/repo", response_model=SetRepoResponse)
async def set_repository(request: SetRepoRequest, user: User = RequireAuth):
    """Set which repository to track for syncing."""
    # Validate format
    if "/" not in request.repo_full_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid repository format. Use 'owner/repo'.",
        )

    with get_db_session() as session:
        connection = (
            session.query(GitHubConnection)
            .filter(GitHubConnection.user_id == user.id)
            .filter(GitHubConnection.is_active == 1)
            .first()
        )

        if not connection:
            raise HTTPException(
                status_code=401,
                detail="No active GitHub connection. Please connect GitHub first.",
            )

        oauth_service = get_github_oauth_service()

        try:
            owner, repo = request.repo_full_name.split("/")

            # Try to use installation token if available
            if connection.installation_id and oauth_service.is_app_configured():
                token_data = await oauth_service.get_installation_access_token(
                    connection.installation_id
                )
                access_token = token_data["token"]
            else:
                access_token = decrypt_token(connection.access_token, ENCRYPTION_KEY)

            async with GitHubService(access_token) as github:
                # Try to get repo info to verify access
                repo_info = await github._make_request("GET", f"/repos/{owner}/{repo}")

            # Update connection with repo info
            connection.repo_full_name = request.repo_full_name
            connection.repo_default_branch = repo_info.get("default_branch", "main")
            connection.repo_is_private = 1 if repo_info.get("private") else 0
            connection.last_commit_sha = None  # Reset to trigger full sync
            session.commit()

            return SetRepoResponse(
                success=True,
                message=f"Repository set to {request.repo_full_name}",
                repo_full_name=request.repo_full_name,
            )

        except Exception as e:
            logger.error(f"Error setting repository: {e}")
            if "404" in str(e) or "not found" in str(e).lower():
                raise HTTPException(
                    status_code=404,
                    detail="Repository not found or you don't have access.",
                )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=SyncResponse)
async def sync_repository(user: User = RequireAuth):
    """Sync the connected repository.

    Fetches dependency files from the connected repo and creates/updates scans.
    """
    sync_service = get_github_sync_service()

    try:
        result = await sync_service.sync_user_repository(user.id)

        if result["success"]:
            return SyncResponse(
                success=True,
                message=result.get("message", "Sync completed"),
                files_found=result["files_found"],
                scans_created=result["scans_created"],
            )
        else:
            return SyncResponse(
                success=False,
                error=result.get("error", "Sync failed"),
                files_found=0,
                scans_created=0,
            )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return SyncResponse(
            success=False,
            error=str(e),
            files_found=0,
            scans_created=0,
        )


@router.post("/sync/toggle-auto")
async def toggle_auto_sync(user: User = RequireAuth):
    """Toggle auto-sync on login setting."""
    with get_db_session() as session:
        connection = (
            session.query(GitHubConnection).filter(GitHubConnection.user_id == user.id).first()
        )

        if not connection:
            raise HTTPException(status_code=404, detail="No GitHub connection found")

        # Toggle
        connection.auto_sync_enabled = 0 if connection.auto_sync_enabled else 1
        session.commit()

        return {
            "success": True,
            "auto_sync_enabled": bool(connection.auto_sync_enabled),
        }


@router.get("/oauth/status")
async def get_oauth_status():
    """Check if GitHub OAuth and GitHub App are configured."""
    oauth_service = get_github_oauth_service()
    return {
        "oauth_configured": oauth_service.is_configured(),
        "app_configured": oauth_service.is_app_configured(),
        "callback_url": oauth_service.callback_url if oauth_service.is_configured() else None,
    }
