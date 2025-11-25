"""GitHub integration API routes."""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.services.github_service import GitHubService, decrypt_token, encrypt_token
from scripts.scan_dependencies import DependencyScanner

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/github",
    tags=["github"],
)

# Get encryption key from environment or use default (change in production)
ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY", "change_this_in_production_123456")


# Pydantic models for request/response
class GitHubTokenRequest(BaseModel):
    """Request model for saving GitHub token."""

    token: str = Field(..., description="GitHub Personal Access Token")


class GitHubTokenResponse(BaseModel):
    """Response model for token operations."""

    success: bool
    message: str
    username: str | None = None


class GitHubRepoRequest(BaseModel):
    """Request model for repository operations."""

    owner: str
    repo: str
    branch: str | None = None


class GitHubImportRequest(BaseModel):
    """Request model for importing dependency file from GitHub."""

    owner: str
    repo: str
    file_path: str
    branch: str | None = None


class GitHubScanRequest(BaseModel):
    """Request model for scanning a GitHub repository file."""

    owner: str
    repo: str
    file_path: str
    branch: str | None = None


@router.post("/save-token", response_model=GitHubTokenResponse)
async def save_github_token(
    request: GitHubTokenRequest,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
) -> GitHubTokenResponse:
    """Save GitHub Personal Access Token for the user.

    Args:
        request: Token request containing the PAT
        db: Database session
        current_user: Current authenticated user

    Returns:
        Response with success status and username
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Test the token first
        async with GitHubService(request.token) as github:
            test_result = await github.test_connection()

        if not test_result["success"]:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid GitHub token: {test_result.get('error', 'Unknown error')}",
            )

        # Encrypt the token
        encrypted_token = encrypt_token(request.token, ENCRYPTION_KEY)

        # Check if user already has a token
        existing = db.execute(
            text("SELECT id FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if existing:
            # Update existing token
            db.execute(
                text(
                    """
                    UPDATE github_integrations
                    SET github_token = :token,
                        github_username = :username,
                        updated_at = :updated_at
                    WHERE user_id = :user_id
                """
                ),
                {
                    "token": encrypted_token,
                    "username": test_result["username"],
                    "updated_at": datetime.utcnow(),
                    "user_id": user_id,
                },
            )
        else:
            # Insert new token
            db.execute(
                text(
                    """
                    INSERT INTO github_integrations
                    (user_id, github_token, github_username, created_at, updated_at)
                    VALUES (:user_id, :token, :username, :created_at, :updated_at)
                """
                ),
                {
                    "user_id": user_id,
                    "token": encrypted_token,
                    "username": test_result["username"],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )

        db.commit()

        return GitHubTokenResponse(
            success=True,
            message="GitHub token saved successfully",
            username=test_result["username"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving GitHub token: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection", response_model=GitHubTokenResponse)
async def test_github_connection(
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
) -> GitHubTokenResponse:
    """Test the stored GitHub token connection.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Response with connection status
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text(
                "SELECT github_token, github_username FROM github_integrations WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            return GitHubTokenResponse(
                success=False,
                message="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Test connection
        async with GitHubService(decrypted_token) as github:
            test_result = await github.test_connection()

        if test_result["success"]:
            return GitHubTokenResponse(
                success=True,
                message="GitHub connection successful",
                username=test_result["username"],
            )
        else:
            return GitHubTokenResponse(
                success=False,
                message=f"GitHub connection failed: {test_result.get('error', 'Unknown error')}",
            )

    except Exception as e:
        logger.error(f"Error testing GitHub connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos")
async def list_repositories(
    type: str = "all",
    sort: str = "updated",
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """List repositories accessible to the authenticated user.

    Args:
        type: Type of repositories to list
        sort: Sort order
        page: Page number
        per_page: Results per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of repositories
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text("SELECT github_token FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=401,
                detail="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Get repositories
        async with GitHubService(decrypted_token) as github:
            repos = await github.list_repositories(
                type=type,
                sort=sort,
                per_page=per_page,
                page=page,
            )

        return {"success": True, "repositories": repos}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{repo}/dependencies")
async def find_dependency_files(
    owner: str,
    repo: str,
    branch: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Find dependency files in a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name (optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of dependency files found
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text("SELECT github_token FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=401,
                detail="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Find dependency files
        async with GitHubService(decrypted_token) as github:
            dependency_files = await github.find_dependency_files(
                owner=owner,
                repo=repo,
                ref=branch,
            )

        return {
            "success": True,
            "repository": f"{owner}/{repo}",
            "branch": branch or "default",
            "dependency_files": dependency_files,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding dependency files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_from_github(
    request: GitHubImportRequest,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Import a dependency file from GitHub.

    Args:
        request: Import request with repository and file details
        db: Database session
        current_user: Current authenticated user

    Returns:
        Import result with file content
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text("SELECT github_token FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=401,
                detail="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Import file
        async with GitHubService(decrypted_token) as github:
            import_result = await github.import_dependency_file(
                owner=request.owner,
                repo=request.repo,
                file_path=request.file_path,
                ref=request.branch,
            )

        if not import_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=import_result.get("error", "Failed to import file"),
            )

        return import_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing from GitHub: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan")
async def scan_github_file(
    request: GitHubScanRequest,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Scan a dependency file from GitHub for vulnerabilities.

    Args:
        request: Scan request with repository and file details
        db: Database session
        current_user: Current authenticated user

    Returns:
        Scan results with vulnerabilities
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text("SELECT github_token FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=401,
                detail="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Import file from GitHub
        async with GitHubService(decrypted_token) as github:
            import_result = await github.import_dependency_file(
                owner=request.owner,
                repo=request.repo,
                file_path=request.file_path,
                ref=request.branch,
            )

        if not import_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=import_result.get("error", "Failed to import file"),
            )

        # Create temporary file for scanning
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f"_{import_result['file_name']}",
            delete=False,
        ) as tmp_file:
            tmp_file.write(import_result["content"])
            tmp_file_path = tmp_file.name

        try:
            # Use existing scanner
            scanner = DependencyScanner(db)
            scan_result = scanner.scan_file(
                file_path=tmp_file_path,
                file_type=import_result["ecosystem"],
                user_id=user_id,
                # Store GitHub metadata
                metadata={
                    "source": "github",
                    "github_repo": f"{request.owner}/{request.repo}",
                    "github_path": request.file_path,
                    "github_branch": request.branch or "main",
                },
            )

            # Clean up temp file
            os.unlink(tmp_file_path)

            return {
                "success": True,
                "scan_id": scan_result["scan_id"],
                "file_name": import_result["file_name"],
                "github_repo": f"{request.owner}/{request.repo}",
                "total_dependencies": scan_result["total_dependencies"],
                "vulnerable_dependencies": scan_result["vulnerable_dependencies"],
                "critical_count": scan_result["critical_count"],
                "high_count": scan_result["high_count"],
                "medium_count": scan_result["medium_count"],
                "low_count": scan_result["low_count"],
            }

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning GitHub file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit")
async def get_rate_limit(
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Get GitHub API rate limit status.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Rate limit information
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Get stored token
        result = db.execute(
            text("SELECT github_token FROM github_integrations WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=401,
                detail="No GitHub token found. Please configure your token first.",
            )

        # Decrypt token
        decrypted_token = decrypt_token(result[0], ENCRYPTION_KEY)

        # Get rate limit
        async with GitHubService(decrypted_token) as github:
            rate_limit = await github.get_rate_limit()

        return {
            "success": True,
            "rate_limit": {
                "limit": rate_limit["limit"],
                "remaining": rate_limit["remaining"],
                "used": rate_limit["used"],
                "reset": rate_limit["reset"].isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/token")
async def delete_github_token(
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Delete the stored GitHub token for the user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success status
    """
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # Delete token
        result = db.execute(
            text("DELETE FROM github_integrations WHERE user_id = :user_id"), {"user_id": user_id}
        )

        db.commit()

        if result.rowcount > 0:
            return {
                "success": True,
                "message": "GitHub token deleted successfully",
            }
        else:
            return {
                "success": False,
                "message": "No GitHub token found to delete",
            }

    except Exception as e:
        logger.error(f"Error deleting GitHub token: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
