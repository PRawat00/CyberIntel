#!/bin/bash

# Start the FastAPI server in development mode

echo "Starting SecureChat API server..."
echo "API will be available at: http://localhost:8000"
echo "Swagger UI: http://localhost:8000/api/docs"
echo ""

python -m api.main
