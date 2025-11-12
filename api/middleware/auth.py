"""
Authentication middleware for Supabase JWT verification.
Production-ready authentication with Supabase using HS256.
Supports dual authentication mode for development.
"""

import base64
import json
import logging
import os
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Get or create Supabase client."""
    global supabase_client

    if supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
            )

        try:
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise RuntimeError(f"Failed to initialize Supabase client: {e}")

    return supabase_client


# HTTP Bearer scheme for extracting JWT from Authorization header
# auto_error=False allows us to handle missing/invalid auth explicitly
security = HTTPBearer(auto_error=False)


class User:
    """User model for authenticated requests."""

    def __init__(self, id: str, email: str | None = None, metadata: dict | None = None):
        self.id = id
        self.email = email
        self.metadata = metadata or {}

    def __repr__(self):
        return f"User(id={self.id}, email={self.email})"


def verify_supabase_jwt(token: str) -> dict:
    """
    Verify Supabase JWT token using HS256 and JWT secret.
    Supabase tokens are signed with HS256 (symmetric encryption).

    Args:
        token: JWT token string from Supabase auth

    Returns:
        User data dict from decoded JWT payload

    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    if not jwt_secret:
        logger.error("SUPABASE_JWT_SECRET not configured in environment")
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET not configured")

    try:
        # Decode and verify JWT token using the secret
        logger.debug(f"Verifying JWT token with HS256 (length: {len(token)})")

        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True, "verify_exp": True},
        )

        # Extract user data from JWT payload
        # Supabase JWT structure: {"sub": "user_id", "email": "...", "user_metadata": {...}, ...}
        user_id = payload.get("sub")
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {})

        if not user_id:
            logger.error("JWT payload missing 'sub' (user ID)")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        user_data = {"id": user_id, "email": email, "user_metadata": user_metadata}

        logger.info(f"JWT verified successfully for user: {user_id}")
        return user_data

    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def is_mock_token(token: str) -> bool:
    """
    Check if a token is a mock authentication token.
    Mock tokens have 'alg': 'MOCK' in their header.
    """
    try:
        # Split token and decode header
        parts = token.split(".")
        if len(parts) != 3:
            return False

        # Decode the header (first part)
        header = parts[0]
        # Add padding if needed
        missing_padding = len(header) % 4
        if missing_padding:
            header += "=" * (4 - missing_padding)

        decoded_header = base64.b64decode(header)
        header_json = json.loads(decoded_header)

        # Check if it's a mock token
        return header_json.get("alg") == "MOCK"
    except Exception as e:
        logger.debug(f"Error checking if token is mock: {e}")
        return False


def verify_mock_token(token: str) -> dict[str, Any]:
    """
    Verify a mock authentication token for development mode.
    Returns user data if valid, raises HTTPException otherwise.
    """
    try:
        # Split and decode the token parts
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid mock token format")

        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += "=" * (4 - missing_padding)

        decoded_payload = base64.b64decode(payload)
        payload_json = json.loads(decoded_payload)

        # Extract user data from mock token
        user_id = payload_json.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid mock token: missing user ID")

        # For mock tokens, use the user ID as email if not provided
        email = payload_json.get("email", f"{user_id}@mock.local")

        user_data = {"id": user_id, "email": email, "user_metadata": {"mock_user": True}}

        logger.info(f"Mock token verified successfully for user: {user_id}")
        return user_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid mock token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> User:
    """
    Verify JWT token and return authenticated user.
    Supports both Supabase JWT and mock tokens based on AUTH_MODE.
    """
    # Handle missing credentials explicitly
    if not credentials:
        logger.warning("No Authorization header provided in request")
        raise HTTPException(
            status_code=401,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    token = credentials.credentials

    # Check authentication mode
    auth_mode = os.getenv("AUTH_MODE", "production")

    try:
        # In development mode, check if it's a mock token first
        if auth_mode == "development" and is_mock_token(token):
            logger.info("Development mode: Processing mock token")
            user_data = verify_mock_token(token)
        else:
            # Verify JWT token with Supabase API
            user_data = verify_supabase_jwt(token)

        # Extract user information
        user_id = user_data.get("id")
        email = user_data.get("email")
        user_metadata = user_data.get("user_metadata", {})

        if not user_id:
            logger.error("Token missing user ID")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        # Create user object
        user = User(
            id=user_id,
            email=email,
            metadata=user_metadata,
        )

        logger.info(f"Authenticated user: {user_id} ({email}) [mode: {auth_mode}]")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> User | None:
    """
    Same as get_current_user but returns None instead of raising exception.
    Use for endpoints that work with or without authentication.
    """
    if not credentials:
        logger.debug("Optional auth: No credentials provided")
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException as e:
        logger.debug(f"Optional auth failed: {e.detail}")
        return None


def verify_token_get_user(token: str) -> User:
    """
    Synchronous version of get_current_user for WebSocket authentication.
    Verifies JWT token and returns User object.

    Args:
        token: JWT token string

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Verify JWT token with Supabase API
        user_data = verify_supabase_jwt(token)

        # Extract user information from Supabase API response
        user_id = user_data.get("id")
        email = user_data.get("email")
        user_metadata = user_data.get("user_metadata", {})

        if not user_id:
            logger.error("Token missing user ID")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

        # Create user object
        user = User(
            id=user_id,
            email=email,
            metadata=user_metadata,
        )

        logger.info(f"Authenticated user (WebSocket): {user_id} ({email})")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


# Dependency for routes that require authentication
RequireAuth = Depends(get_current_user)

# Dependency for routes that optionally use authentication
OptionalAuth = Depends(get_current_user_optional)
