"""GitHub sync service for syncing repositories and creating scans.

This module provides functionality to:
- Sync connected GitHub repositories
- Detect and fetch dependency files
- Create scans from GitHub-sourced files
"""

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from api.services.github_service import GitHubService, decrypt_token
from database.db import get_db_manager, get_db_session
from database.models import GitHubConnection, Scan
from scripts.scan_dependencies import DependencyScanner

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """Service for syncing GitHub repositories."""

    def __init__(self):
        """Initialize sync service."""
        self.encryption_key = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY", "default-dev-key")

    async def sync_user_repository(self, user_id: str) -> dict:
        """Sync the connected repository for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with sync results
        """
        with get_db_session() as session:
            # Get user's GitHub connection
            connection = (
                session.query(GitHubConnection)
                .filter(GitHubConnection.user_id == user_id)
                .filter(GitHubConnection.is_active == 1)
                .first()
            )

            if not connection:
                return {
                    "success": False,
                    "error": "No active GitHub connection found",
                    "files_found": 0,
                    "scans_created": 0,
                }

            if not connection.repo_full_name:
                return {
                    "success": False,
                    "error": "No repository selected",
                    "files_found": 0,
                    "scans_created": 0,
                }

            try:
                # Decrypt access token
                access_token = decrypt_token(connection.access_token, self.encryption_key)

                # Parse repo info
                owner, repo = connection.repo_full_name.split("/")

                # Use GitHub service to find and import dependency files
                async with GitHubService(access_token) as github:
                    # Find dependency files
                    dep_files = await github.find_dependency_files(
                        owner, repo, ref=connection.repo_default_branch
                    )

                    if not dep_files:
                        # Update connection status
                        connection.last_sync_at = datetime.utcnow()
                        connection.sync_error = None
                        session.commit()

                        return {
                            "success": True,
                            "files_found": 0,
                            "scans_created": 0,
                            "message": "No dependency files found in repository",
                        }

                    # Get current branch's latest commit
                    try:
                        # Get the default branch ref
                        repo_info = await github._make_request("GET", f"/repos/{owner}/{repo}")
                        default_branch = repo_info.get("default_branch", "main")

                        branch_info = await github._make_request(
                            "GET", f"/repos/{owner}/{repo}/branches/{default_branch}"
                        )
                        current_commit_sha = branch_info.get("commit", {}).get("sha")
                    except Exception as e:
                        logger.warning(f"Could not get commit SHA: {e}")
                        current_commit_sha = None

                    scans_created = 0

                    for dep_file in dep_files:
                        try:
                            # Check if we already have a scan for this file+commit
                            existing_scan = (
                                session.query(Scan)
                                .filter(Scan.user_id == user_id)
                                .filter(Scan.source == "github")
                                .filter(Scan.github_repo == connection.repo_full_name)
                                .filter(Scan.github_path == dep_file["path"])
                                .filter(Scan.github_commit_sha == current_commit_sha)
                                .first()
                            )

                            if existing_scan and current_commit_sha:
                                logger.info(
                                    f"Skipping {dep_file['path']} - already scanned at commit {current_commit_sha}"
                                )
                                continue

                            # Import and scan the file
                            scan_result = await self._scan_github_file(
                                github=github,
                                owner=owner,
                                repo=repo,
                                file_info=dep_file,
                                user_id=user_id,
                                repo_full_name=connection.repo_full_name,
                                commit_sha=current_commit_sha,
                                session=session,
                            )

                            if scan_result.get("success"):
                                scans_created += 1

                        except Exception as e:
                            logger.error(f"Error scanning {dep_file['path']}: {e}")
                            continue

                    # Update connection status
                    connection.last_sync_at = datetime.utcnow()
                    connection.last_commit_sha = current_commit_sha
                    connection.sync_error = None
                    session.commit()

                    return {
                        "success": True,
                        "files_found": len(dep_files),
                        "scans_created": scans_created,
                    }

            except Exception as e:
                logger.error(f"Sync failed for user {user_id}: {e}")

                # Update connection with error
                connection.sync_error = str(e)
                session.commit()

                return {
                    "success": False,
                    "error": str(e),
                    "files_found": 0,
                    "scans_created": 0,
                }

    async def _scan_github_file(
        self,
        github: GitHubService,
        owner: str,
        repo: str,
        file_info: dict,
        user_id: str,
        repo_full_name: str,
        commit_sha: str | None,
        session,
    ) -> dict:
        """Scan a single dependency file from GitHub.

        Args:
            github: GitHubService instance
            owner: Repository owner
            repo: Repository name
            file_info: File information from find_dependency_files
            user_id: User ID
            repo_full_name: Full repository name (owner/repo)
            commit_sha: Current commit SHA
            session: Database session

        Returns:
            Dictionary with scan results
        """
        tmp_dir = None
        tmp_path = None

        try:
            # Import the file content
            import_result = await github.import_dependency_file(owner, repo, file_info["path"])

            if not import_result.get("success"):
                return {"success": False, "error": import_result.get("error")}

            content = import_result["content"]
            file_name = import_result["file_name"]

            # Save to temporary file for scanning
            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, file_name)

            with open(tmp_path, "w") as f:
                f.write(content)

            # Get the database manager for the scanner
            db_manager = get_db_manager()

            # Initialize scanner
            scanner = DependencyScanner(session_factory=db_manager.SessionLocal)

            # Scan the file
            result = scanner.scan_file(Path(tmp_path), user_id=user_id, session=session)
            scan_id = result["scan_id"]

            # Update the scan with GitHub source info
            scan = session.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.source = "github"
                scan.github_repo = repo_full_name
                scan.github_path = file_info["path"]
                scan.github_commit_sha = commit_sha
                session.commit()

            logger.info(f"Created scan {scan_id} for {file_info['path']} from GitHub")

            return {
                "success": True,
                "scan_id": scan_id,
                "file_path": file_info["path"],
            }

        except Exception as e:
            logger.error(f"Error scanning GitHub file {file_info['path']}: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Clean up temp files
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.debug(f"Failed to clean up temp file {tmp_path}: {e}")
            if tmp_dir and os.path.exists(tmp_dir):
                try:
                    os.rmdir(tmp_dir)
                except Exception as e:
                    logger.debug(f"Failed to clean up temp dir {tmp_dir}: {e}")


# Singleton instance
_sync_service = None


def get_github_sync_service() -> GitHubSyncService:
    """Get the singleton sync service instance.

    Returns:
        The GitHubSyncService singleton
    """
    global _sync_service
    if _sync_service is None:
        _sync_service = GitHubSyncService()
    return _sync_service
