"""
Authentication middleware for Supabase JWT verification.
Supports both Supabase auth and mock users for local development.
"""

import base64
import json
import logging
import os

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Initialize Supabase client (only if credentials are set)
supabase_client: Client | None = None


def get_supabase_client() -> Client | None:
    """Get or create Supabase client."""
    global supabase_client

    if supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            try:
                supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")
                supabase_client = None
        else:
            logger.info("Supabase credentials not set, auth disabled (local dev mode)")

    return supabase_client


# HTTP Bearer scheme for extracting JWT from Authorization header
security = HTTPBearer(auto_error=False)


class User:
    """User model for authenticated requests."""

    def __init__(self, id: str, email: str | None = None, metadata: dict | None = None):
        self.id = id
        self.email = email
        self.metadata = metadata or {}

    def __repr__(self):
        return f"User(id={self.id}, email={self.email})"


# Mock users for local development (matches frontend mock-auth.ts)
MOCK_USERS = {
    "00000000-0000-0000-0000-000000000001": User(
        id="00000000-0000-0000-0000-000000000001",
        email="local@test.dev",
        metadata={"provider": "email", "full_name": "Local Test User"},
    ),
    "00000000-0000-0000-0000-000000000002": User(
        id="00000000-0000-0000-0000-000000000002",
        email="demo@example.com",
        metadata={"provider": "email", "full_name": "Demo User"},
    ),
    "00000000-0000-0000-0000-000000000003": User(
        id="00000000-0000-0000-0000-000000000003",
        email="admin@cyberintel.dev",
        metadata={"provider": "email", "full_name": "Admin User"},
    ),
    "00000000-0000-0000-0000-000000000004": User(
        id="00000000-0000-0000-0000-000000000004",
        email="testuser@example.com",
        metadata={"provider": "email", "full_name": "Test User"},
    ),
}

# Default mock user (fallback)
MOCK_USER = MOCK_USERS["00000000-0000-0000-0000-000000000001"]


def parse_mock_jwt(token: str) -> str | None:
    """
    Parse mock JWT token and extract user ID from payload.

    Mock tokens have format: header.payload.signature
    Payload contains: {"sub": "user_id", "exp": ..., "iat": ...}

    Returns user_id or None if invalid.
    """
    try:
        # Split token into parts
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (second part)
        payload_encoded = parts[1]

        # Add padding if needed for base64 decoding
        padding = 4 - (len(payload_encoded) % 4)
        if padding != 4:
            payload_encoded += "=" * padding

        # Decode base64
        payload_json = base64.b64decode(payload_encoded).decode("utf-8")
        payload = json.loads(payload_json)

        # Extract user ID from 'sub' field
        user_id = payload.get("sub")

        if user_id:
            logger.debug(f"Parsed mock JWT token, user_id: {user_id}")
            return user_id

        return None

    except Exception as e:
        logger.debug(f"Failed to parse mock JWT token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> User:
    """
    Verify JWT token and return authenticated user.
    Falls back to mock user if Supabase is not configured (local dev).
    """

    client = get_supabase_client()

    # If no Supabase client (local dev mode), parse mock JWT token
    if client is None:
        logger.debug("Local dev mode: parsing mock JWT token")

        # Check if we have credentials (Authorization header)
        if credentials is None:
            logger.debug("No credentials provided, using default mock user")
            return MOCK_USER

        # Extract token
        token = credentials.credentials

        # Parse mock JWT to get user ID
        user_id = parse_mock_jwt(token)

        if user_id and user_id in MOCK_USERS:
            user = MOCK_USERS[user_id]
            logger.debug(f"Authenticated as mock user: {user}")
            return user
        else:
            logger.debug(
                f"Invalid mock token or unknown user_id: {user_id}, using default mock user"
            )
            return MOCK_USER

    # If no credentials provided, check if we allow anonymous access
    if credentials is None:
        # For local dev, allow anonymous as mock user
        if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
            logger.debug("Using mock user (anonymous access allowed)")
            return MOCK_USER

        raise HTTPException(
            status_code=401, detail="Authentication required. Please provide a valid JWT token."
        )

    # Extract token
    token = credentials.credentials

    try:
        # Verify token with Supabase
        response = client.auth.get_user(token)

        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Extract user information
        user = User(
            id=response.user.id,
            email=response.user.email,
            metadata=response.user.user_metadata or {},
        )

        logger.debug(f"Authenticated user: {user}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(  # noqa: B904
            status_code=401, detail=f"Token verification failed: {str(e)}"
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> User | None:
    """
    Same as get_current_user but returns None instead of raising exception.
    Use for endpoints that work with or without authentication.
    """
    try:
        return await get_current_user(credentials)
    except HTTPException:
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
    client = get_supabase_client()

    # If no Supabase client (local dev mode), parse mock JWT token
    if client is None:
        logger.debug("Local dev mode: parsing mock JWT token")

        # Parse mock JWT to get user ID
        user_id = parse_mock_jwt(token)

        if user_id and user_id in MOCK_USERS:
            user = MOCK_USERS[user_id]
            logger.debug(f"Authenticated as mock user: {user}")
            return user
        else:
            logger.debug(
                f"Invalid mock token or unknown user_id: {user_id}, using default mock user"
            )
            return MOCK_USER

    try:
        # Verify token with Supabase
        response = client.auth.get_user(token)

        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Extract user information
        user = User(
            id=response.user.id,
            email=response.user.email,
            metadata=response.user.user_metadata or {},
        )

        logger.debug(f"Authenticated user: {user}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(  # noqa: B904
            status_code=401, detail=f"Token verification failed: {str(e)}"
        )


# Dependency for routes that require authentication
RequireAuth = Depends(get_current_user)

# Dependency for routes that optionally use authentication
OptionalAuth = Depends(get_current_user_optional)
