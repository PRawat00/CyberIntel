"""
Authentication endpoints for development and production.
Supports both mock authentication (development) and Supabase (production).
"""

import base64
import json
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.middleware.auth import User, get_current_user

router = APIRouter()


class Token(BaseModel):
    """OAuth2 token response model."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 standard token type, not a password


class AuthStatus(BaseModel):
    """Authentication status response."""

    auth_mode: str
    mock_auth_enabled: bool
    supabase_configured: bool
    current_user: str | None = None


def generate_mock_token(user_id: str, email: str = None) -> str:
    """
    Generate a mock JWT token for development mode.

    Args:
        user_id: The user ID to encode in the token
        email: Optional email address

    Returns:
        A mock JWT token string
    """
    # Create header
    header = {"alg": "MOCK", "typ": "JWT"}

    # Create payload with expiration
    payload = {
        "sub": user_id,
        "email": email or f"{user_id}@mock.local",
        "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }

    # Create signature (mock)
    signature = f"mock-signature-{user_id}"

    # Encode parts
    header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature_b64 = base64.b64encode(signature.encode()).decode().rstrip("=")

    # Combine into token
    token = f"{header_b64}.{payload_b64}.{signature_b64}"

    return token


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.

    In development mode (AUTH_MODE=development):
    - Accepts mock credentials from env vars:
      MOCK_AUTH_USERNAME (default: local@test.dev)
      MOCK_AUTH_PASSWORD (default: password123)

    In production mode:
    - Requires valid Supabase credentials
    """
    auth_mode = os.getenv("AUTH_MODE", "production")

    # Development mode - accept mock credentials
    if auth_mode == "development":
        # Check for mock credentials from environment variables
        mock_username = os.getenv("MOCK_AUTH_USERNAME", "local@test.dev")
        mock_password = os.getenv("MOCK_AUTH_PASSWORD", "password123")  # pragma: allowlist secret

        if (
            form_data.username == mock_username and form_data.password == mock_password
        ):  # noqa: S105
            # Generate mock token
            token = generate_mock_token(user_id="mock-user-123", email=mock_username)

            return Token(access_token=token, token_type="bearer")  # noqa: S106

        # In development, also try Supabase if mock credentials don't match
        # This allows using both auth methods in development

    # Production mode or Supabase fallback in development
    # Here you would integrate with Supabase authentication
    # For now, return an error since Supabase integration would require more setup

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/status", response_model=AuthStatus)
async def auth_status():
    """
    Get current authentication configuration status.

    Returns information about:
    - Current auth mode (development/production)
    - Whether mock auth is enabled
    - Whether Supabase is configured
    """
    auth_mode = os.getenv("AUTH_MODE", "production")

    return AuthStatus(
        auth_mode=auth_mode,
        mock_auth_enabled=(auth_mode == "development"),
        supabase_configured=bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_JWT_SECRET")),
    )


@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    This endpoint requires authentication and returns the current user's details.
    """
    return {
        "id": user.id,
        "email": user.email,
        "metadata": user.metadata,
        "auth_mode": os.getenv("AUTH_MODE", "production"),
    }


@router.post("/test-login")
async def test_login():
    """
    Test endpoint to get a development token quickly.
    Only works in development mode.

    Returns a token for the test user without requiring credentials.
    """
    auth_mode = os.getenv("AUTH_MODE", "production")

    if auth_mode != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test login only available in development mode",
        )

    # Generate test token
    token = generate_mock_token(user_id="test-user-123", email="test@example.com")

    return {
        "message": "Test token generated for development",
        "token": token,
        "usage": "Use this token in Authorization header: Bearer <token>",
    }
