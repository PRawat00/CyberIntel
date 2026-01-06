#!/bin/bash

# CyberIntel Summarizer - Environment Switcher
# Usage: ./scripts/switch-env.sh [local|production]

set -e  # Exit on error

if [ "$1" != "local" ] && [ "$1" != "production" ]; then
    echo "Usage: ./scripts/switch-env.sh [local|production]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/switch-env.sh local       # Switch to local development"
    echo "  ./scripts/switch-env.sh production  # Switch to production"
    exit 1
fi

ENV=$1
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "======================================="
echo "  Environment Switcher"
echo "======================================="
echo ""
echo "Switching to: $ENV"
echo ""

# Check if environment files exist
if [ ! -f "$ROOT_DIR/api/.env.$ENV" ]; then
    echo "Error: $ROOT_DIR/api/.env.$ENV not found!"
    echo "Please create this file before switching."
    exit 1
fi

if [ "$ENV" = "local" ]; then
    FRONTEND_ENV_FILE="$ROOT_DIR/frontend/.env.local.dev"
    # Fallback to .env.local if .env.local.dev doesn't exist
    if [ ! -f "$FRONTEND_ENV_FILE" ]; then
        FRONTEND_ENV_FILE="$ROOT_DIR/frontend/.env.local"
    fi
else
    FRONTEND_ENV_FILE="$ROOT_DIR/frontend/.env.$ENV"
fi

if [ ! -f "$FRONTEND_ENV_FILE" ]; then
    echo "Warning: $FRONTEND_ENV_FILE not found!"
    echo "Frontend environment may not be configured correctly."
fi

# Backend
echo "[1/2] Configuring backend..."
cp "$ROOT_DIR/api/.env.$ENV" "$ROOT_DIR/api/.env"
echo "      ✓ Copied api/.env.$ENV -> api/.env"

# Frontend
if [ -f "$FRONTEND_ENV_FILE" ]; then
    echo "[2/2] Configuring frontend..."
    cp "$FRONTEND_ENV_FILE" "$ROOT_DIR/frontend/.env.local"
    echo "      ✓ Copied frontend/.env.$ENV -> frontend/.env.local"
else
    echo "[2/2] Skipping frontend (file not found)"
fi

echo ""
echo "======================================="
echo "  Environment switched to: $ENV"
echo "======================================="
echo ""

# Verification
echo "Verification:"
AUTH_MODE=$(grep '^AUTH_MODE=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2 || echo "NOT SET")
DEBUG=$(grep '^DEBUG=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2 || echo "NOT SET")
API_URL=$(grep '^NEXT_PUBLIC_API_URL=' "$ROOT_DIR/frontend/.env.local" 2>/dev/null | cut -d'=' -f2 || echo "NOT SET")

echo "  Backend AUTH_MODE: $AUTH_MODE"
echo "  Backend DEBUG: $DEBUG"
echo "  Frontend API URL: $API_URL"
echo ""

# Warnings
if [ "$ENV" = "production" ] && [ "$DEBUG" = "true" ]; then
    echo "⚠️  WARNING: DEBUG=true in production mode!"
    echo ""
fi

if [ "$ENV" = "production" ] && [ "$AUTH_MODE" = "development" ]; then
    echo "⚠️  WARNING: AUTH_MODE=development in production!"
    echo ""
fi

echo "IMPORTANT:"
echo "  • Restart your servers for changes to take effect"
echo "  • Kill running processes: lsof -ti:8000 | xargs kill -9"
echo "  • Run ./scripts/check-env.sh to verify configuration"
echo ""
