# SecureChat API

FastAPI backend for the SecureChat dependency vulnerability scanner.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Development mode (auto-reload)
python -m api.main

# Or with uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 3. View API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## API Endpoints

### Scans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scans` | Upload and scan a dependency file |
| GET | `/api/scans` | List all scans (paginated) |
| GET | `/api/scans/{id}` | Get detailed scan results |
| GET | `/api/scans/{id}/dependencies` | Get scan dependencies (filtered) |
| GET | `/api/scans/{id}/export` | Export scan (json/csv/html) |
| DELETE | `/api/scans/{id}` | Delete a scan |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Get dashboard statistics |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API information |

## Example Usage

### Upload and Scan a File

```bash
curl -X POST "http://localhost:8000/api/scans" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@package.json"
```

Response:
```json
{
  "id": 1,
  "file_name": "package.json",
  "file_type": "npm",
  "scan_date": "2025-11-08T10:30:00",
  "total_dependencies": 47,
  "vulnerable_dependencies": 12,
  "total_cves": 15,
  "severity_counts": {
    "critical": 3,
    "high": 5,
    "medium": 4,
    "low": 3
  },
  "dependencies": [...]
}
```

### List Scans

```bash
curl "http://localhost:8000/api/scans?page=1&per_page=20"
```

### Get Scan Details

```bash
curl "http://localhost:8000/api/scans/1"
```

### Export Scan

```bash
# JSON
curl "http://localhost:8000/api/scans/1/export?format=json" > scan.json

# CSV
curl "http://localhost:8000/api/scans/1/export?format=csv" > scan.csv

# HTML
curl "http://localhost:8000/api/scans/1/export?format=html" > scan.html
```

### Get Statistics

```bash
curl "http://localhost:8000/api/stats"
```

## File Upload Constraints

- **Max file size**: 1MB
- **Allowed extensions**: `.json`, `.txt`, `.lock`, `.in`, `.toml`, `.mod`, `.sum`
- **Supported formats**:
  - `package.json`, `package-lock.json` (npm)
  - `requirements.txt`, `Pipfile` (Python)
  - `go.mod`, `go.sum` (Go) - coming soon
  - Other formats - coming soon

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:3001`
- `http://127.0.0.1:3000`

To add more origins, update `api/main.py`.

## Error Handling

All errors return JSON with this format:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {}
}
```

## Development

### Run with Auto-reload

```bash
python -m api.main
```

### Run Tests

```bash
# Test API endpoints
pytest tests/test_api.py -v

# Test with coverage
pytest tests/test_api.py --cov=api
```

## Production Deployment

### With Gunicorn

```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### With Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///./cyberintel.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourproductionurl.com
```

## Next Steps

1. Start the API server
2. Test endpoints with Swagger UI
3. Build the Next.js frontend
4. Connect frontend to API
5. Deploy!
