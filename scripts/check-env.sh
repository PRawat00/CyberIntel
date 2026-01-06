#!/bin/bash

# CyberIntel Summarizer - Environment Configuration Checker
# Usage: ./scripts/check-env.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================"
echo "  Environment Configuration Check"
echo "========================================"
echo ""

HAS_ISSUES=0

# Backend Configuration
echo "BACKEND CONFIGURATION (api/.env)"
echo "----------------------------------------"

if [ -f "$ROOT_DIR/api/.env" ]; then
    AUTH_MODE=$(grep '^AUTH_MODE=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2)
    DEBUG=$(grep '^DEBUG=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2)
    ALLOW_MOCK=$(grep '^ALLOW_MOCK_AUTH=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2)
    DB_URL=$(grep '^DATABASE_URL=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2)
    FRONTEND_URL=$(grep '^FRONTEND_URL=' "$ROOT_DIR/api/.env" 2>/dev/null | cut -d'=' -f2)

    # Determine database type
    if [[ "$DB_URL" == sqlite* ]]; then
        DB_TYPE="SQLite (local)"
    elif [[ "$DB_URL" == postgresql* ]]; then
        DB_TYPE="PostgreSQL (likely production)"
    else
        DB_TYPE="Unknown"
    fi

    echo "  AUTH_MODE:        $AUTH_MODE"
    echo "  DEBUG:            $DEBUG"
    echo "  ALLOW_MOCK_AUTH:  $ALLOW_MOCK"
    echo "  DATABASE:         $DB_TYPE"
    echo "  FRONTEND_URL:     $FRONTEND_URL"

    # Detect environment
    if [ "$AUTH_MODE" = "development" ]; then
        BACKEND_ENV="LOCAL"
    elif [ "$AUTH_MODE" = "production" ]; then
        BACKEND_ENV="PRODUCTION"
    else
        BACKEND_ENV="UNKNOWN"
        HAS_ISSUES=1
    fi

    echo "  Detected:         $BACKEND_ENV"

    # Check for issues
    if [ "$AUTH_MODE" = "production" ] && [ "$DEBUG" = "true" ]; then
        echo "  ⚠️  WARNING: DEBUG=true in production mode!"
        HAS_ISSUES=1
    fi

    if [ "$AUTH_MODE" = "production" ] && [ "$ALLOW_MOCK" = "true" ]; then
        echo "  ⚠️  WARNING: ALLOW_MOCK_AUTH=true in production!"
        HAS_ISSUES=1
    fi

    if [ "$AUTH_MODE" = "development" ] && [[ "$DB_URL" == postgresql* ]]; then
        echo "  ⚠️  WARNING: Using PostgreSQL in development mode"
        echo "     (This is OK if intentional, but usually SQLite is used for local)"
    fi
else
    echo "  ❌ Backend .env file not found at: $ROOT_DIR/api/.env"
    echo "     Run: ./scripts/switch-env.sh local"
    BACKEND_ENV="NONE"
    HAS_ISSUES=1
fi

echo ""

# Frontend Configuration
echo "FRONTEND CONFIGURATION (frontend/.env.local)"
echo "----------------------------------------"

if [ -f "$ROOT_DIR/frontend/.env.local" ]; then
    API_URL=$(grep '^NEXT_PUBLIC_API_URL=' "$ROOT_DIR/frontend/.env.local" 2>/dev/null | cut -d'=' -f2)
    WS_URL=$(grep '^NEXT_PUBLIC_WS_URL=' "$ROOT_DIR/frontend/.env.local" 2>/dev/null | cut -d'=' -f2)
    SUPABASE_URL=$(grep '^NEXT_PUBLIC_SUPABASE_URL=' "$ROOT_DIR/frontend/.env.local" 2>/dev/null | cut -d'=' -f2)

    echo "  API_URL:          $API_URL"
    echo "  WS_URL:           $WS_URL"
    echo "  SUPABASE_URL:     $SUPABASE_URL"

    # Detect environment
    if [[ "$API_URL" == *"localhost"* ]] || [[ "$API_URL" == *"127.0.0.1"* ]]; then
        FRONTEND_ENV="LOCAL"
    else
        FRONTEND_ENV="PRODUCTION"
    fi

    echo "  Detected:         $FRONTEND_ENV"

    # Check for mismatches
    if [ "$API_URL" = "" ]; then
        echo "  ⚠️  WARNING: NEXT_PUBLIC_API_URL is not set!"
        HAS_ISSUES=1
    fi

    if [ "$SUPABASE_URL" = "" ]; then
        echo "  ⚠️  WARNING: NEXT_PUBLIC_SUPABASE_URL is not set!"
        HAS_ISSUES=1
    fi
else
    echo "  ❌ Frontend .env.local file not found at: $ROOT_DIR/frontend/.env.local"
    echo "     Run: ./scripts/switch-env.sh local"
    FRONTEND_ENV="NONE"
    HAS_ISSUES=1
fi

echo ""

# Environment Mismatch Check
echo "ENVIRONMENT CONSISTENCY"
echo "----------------------------------------"

if [ "$BACKEND_ENV" != "NONE" ] && [ "$FRONTEND_ENV" != "NONE" ]; then
    if [ "$BACKEND_ENV" = "$FRONTEND_ENV" ]; then
        echo "  ✅ Backend and frontend environments match: $BACKEND_ENV"
    else
        echo "  ⚠️  MISMATCH DETECTED!"
        echo "     Backend:  $BACKEND_ENV"
        echo "     Frontend: $FRONTEND_ENV"
        echo ""
        echo "     This usually means:"
        if [ "$BACKEND_ENV" = "LOCAL" ] && [ "$FRONTEND_ENV" = "PRODUCTION" ]; then
            echo "     • Backend is configured for local but frontend points to production API"
            echo "     • Frontend will try to connect to production instead of localhost:8000"
        elif [ "$BACKEND_ENV" = "PRODUCTION" ] && [ "$FRONTEND_ENV" = "LOCAL" ]; then
            echo "     • Backend is configured for production but frontend points to localhost"
            echo "     • This setup doesn't make sense - switch one or the other"
        fi
        echo ""
        echo "     Fix by running: ./scripts/switch-env.sh [local|production]"
        HAS_ISSUES=1
    fi
else
    echo "  ⚠️  Cannot check consistency - missing environment files"
    HAS_ISSUES=1
fi

echo ""

# Running Services Check
echo "RUNNING SERVICES"
echo "----------------------------------------"

BACKEND_RUNNING=$(lsof -ti:8000 2>/dev/null)
FRONTEND_RUNNING=$(lsof -ti:3000 2>/dev/null)

if [ -n "$BACKEND_RUNNING" ]; then
    echo "  Backend (port 8000):  ✓ Running (PID: $BACKEND_RUNNING)"
else
    echo "  Backend (port 8000):  ✗ Not running"
fi

if [ -n "$FRONTEND_RUNNING" ]; then
    echo "  Frontend (port 3000): ✓ Running (PID: $FRONTEND_RUNNING)"
else
    echo "  Frontend (port 3000): ✗ Not running"
fi

echo ""

# Summary
echo "========================================"
echo "  SUMMARY"
echo "========================================"

if [ $HAS_ISSUES -eq 0 ]; then
    echo "✅ All checks passed! Environment is correctly configured."
    echo ""
    echo "Current environment: $BACKEND_ENV"

    if [ -n "$BACKEND_RUNNING" ] || [ -n "$FRONTEND_RUNNING" ]; then
        echo ""
        echo "NOTE: Servers are running. If you made config changes,"
        echo "      restart them for changes to take effect:"
        echo ""
        echo "  # Kill servers"
        echo "  lsof -ti:8000 | xargs kill -9"
        echo "  lsof -ti:3000 | xargs kill -9"
        echo ""
        echo "  # Restart backend"
        echo "  python -m uvicorn api.main:app --reload --port 8000"
        echo ""
        echo "  # Restart frontend"
        echo "  cd frontend && npm run dev"
    fi
else
    echo "⚠️  Issues detected. Please review the warnings above."
    echo ""
    echo "Quick fixes:"
    echo "  • Switch to local:      ./scripts/switch-env.sh local"
    echo "  • Switch to production: ./scripts/switch-env.sh production"
    echo "  • Restart servers after switching"
fi

echo ""
