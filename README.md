# Allure Harbor

Internal FastAPI service that accepts a ZIP of Allure results, generates a static HTML report, and serves it over HTTP so QA teams can share a URL instead of files.

Anyone who can reach the VM (or other host) can upload, list, delete, and view reports. There is no API key. Lock access at the network layer (VPN, firewall, or private subnet).

Do not use `allure serve`. This service runs `allure generate` and hosts the output.

## Requirements

- Python 3.12+
- Allure Commandline 2.x and a JRE 17+ (or Docker)

## Quick start (local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:create_app --factory --reload
```

Open `http://localhost:8000/docs` for Swagger UI.

## QA usage

Zip your `allure-results` directory (the JSON/XML output from pytest-allure or a Java adapter), not a pre-built `allure-report` folder.

```bash
curl -X POST http://localhost:8000/api/v1/reports ^
  -F "file=@allure-results.zip" ^
  -F "project=checkout-suite" ^
  -F "name=nightly"
```

Example response:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "project": "checkout-suite",
  "name": "nightly",
  "status": "ready",
  "created_at": "2026-09-09T06:00:00+00:00",
  "error_message": null,
  "size_bytes": 20480,
  "view_url": "http://localhost:8000/reports/3fa85f64-5717-4562-b3fc-2c963f66afa6/",
  "expires_at": null
}
```

Open `view_url` in a browser.

```bash
curl http://localhost:8000/api/v1/reports
curl http://localhost:8000/api/v1/reports/{id}
curl -X DELETE http://localhost:8000/api/v1/reports/{id}
curl http://localhost:8000/health
```

## Docker (VM)

```bash
copy .env.example .env
docker compose up --build -d
```

The API listens on port 8000. Nginx on port 80 raises the upload cap to 500 MB. Point `ALLURE_HARBOR_PUBLIC_BASE_URL` at the VM hostname so `view_url` links are correct.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/reports` | Upload ZIP, generate report |
| GET | `/api/v1/reports` | Paginated list (`page`, `page_size`, `project`) |
| GET | `/api/v1/reports/{id}` | Report metadata |
| DELETE | `/api/v1/reports/{id}` | Delete metadata and files |
| GET | `/reports/{id}/` | Generated HTML report |
| GET | `/health` | Liveness plus Allure CLI version |

Errors use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": []
  }
}
```

## Configuration

Environment variables use the `ALLURE_HARBOR_` prefix:

| Variable | Default | Meaning |
|---|---|---|
| `ALLURE_HARBOR_DATA_DIR` | `./data` | Report files and SQLite DB |
| `ALLURE_HARBOR_MAX_UPLOAD_MB` | `200` | Compressed ZIP size cap |
| `ALLURE_HARBOR_MAX_ZIP_FILES` | `10000` | Zip-bomb file count cap |
| `ALLURE_HARBOR_MAX_UNCOMPRESSED_MB` | `1000` | Zip-bomb uncompressed size cap |
| `ALLURE_HARBOR_ALLURE_BIN` | `allure` | Allure CLI path |
| `ALLURE_HARBOR_ALLURE_TIMEOUT_SECONDS` | `300` | Generate timeout |
| `ALLURE_HARBOR_PUBLIC_BASE_URL` | `http://localhost:8000` | Base for `view_url` |

## Tests

```bash
pytest
pytest --cov=app --cov-report=html
ruff check .
mypy app/
```
