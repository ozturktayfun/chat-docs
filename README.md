# Document Chat Assistant

An AI-powered FastAPI backend that lets authenticated users upload PDFs, parse them into structured text, and chat with the document contents using Google's Gemini models.

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running with Docker](#running-with-docker)
- [Running Locally (Optional)](#running-locally-optional)
- [Environment Variables](#environment-variables)
- [API Usage Examples](#api-usage-examples)
- [Testing](#testing)
- [Known Issues & Limitations](#known-issues--limitations)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)

## Features
- JWT-secured authentication for user registration and login.
- PostgreSQL-powered relational data for user details and selected PDFs.
- MongoDB GridFS storage for PDF binaries, with asynchronous access via Motor.
- PDF parsing powered by `PyPDF2`, exposing metadata and extracted text length.
- Chat endpoint backed by Google Gemini models to answer questions about uploaded PDFs.
- Dockerized deployment with health checks and configurable environment settings.

## Architecture Overview
```
FastAPI (app/main.py)
├── Core configuration & logging (`app/core/*`)
├── Dependency providers (`app/api/deps.py`)
├── API routers (`app/api/*`)
│   ├── /register, /login (auth)
│   ├── /pdf-upload, /pdf-list, /pdf-select, /pdf-parse (pdf)
│   └── /pdf-chat, /chat-history (chat)
├── PostgreSQL integration (`app/db/postgres.py`, SQLAlchemy models)
├── MongoDB integration (`app/db/mongodb.py`, GridFS)
└── Services layer (`app/services/*`)
```

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized run)
- Access to PostgreSQL and MongoDB instances (Docker services are provided)
- Google Gemini API key (optional but required for LLM chat functionality)

## Setup & Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/ozturktayfun/chat-docs.git
   cd chat-docs
   ```
2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Copy the example environment file**
   ```bash
   cp .env.example .env
   ```
5. **Fill in `.env` values** (see [Environment Variables](#environment-variables)).

## Running with Docker
1. **Build and start the stack**
   ```bash
   docker-compose up --build -d
   ```
2. **Inspect containers**
   ```bash
   docker-compose ps
   ```
3. **Tail logs**
   ```bash
   docker-compose logs -f app
   ```
4. **Access the API**
   - Base URL: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

To stop everything, run `docker-compose down`.

## Running Locally (Optional)
1. Ensure PostgreSQL and MongoDB are running and match the URLs in `.env`.
2. Apply database migrations or let SQLAlchemy auto-create tables on first start.
3. Launch the API with Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```
4. The service will listen on `http://127.0.0.1:8000` by default.

## Environment Variables
The application reads configuration from environment variables via `pydantic-settings`. Create a `.env` file with at least the following values:

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Override default application name | `Document Chat Assistant` |
| `DEBUG` | Enable debug logging (`true`/`false`) | `true` |
| `SECRET_KEY` | JWT signing secret (required for auth) | `super-secret-key` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | `60` |
| `POSTGRES_URL` | SQLAlchemy URL for PostgreSQL | `postgresql://postgres:postgres@postgres:5432/postgres` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://mongo:27017` |
| `MONGODB_DB_NAME` | MongoDB database name | `chat-docs` |
| `GEMINI_API_KEY` | Google Gemini API key (required for LLM chat) | `AIza...` |
| `GEMINI_MODEL` | Gemini model identifier | `gemini-1.5-flash-latest` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `MAX_FILE_SIZE` | Max upload size in bytes | `10485760` |
| `ALLOWED_FILE_TYPES` | Comma-separated MIME types | `application/pdf` |

### Example `.env`
```dotenv
APP_NAME="Document Chat Assistant"
DEBUG=true
SECRET_KEY="replace-me"
ACCESS_TOKEN_EXPIRE_MINUTES=60
POSTGRES_URL="postgresql://postgres:postgres@postgres:5432/postgres"
MONGODB_URL="mongodb://mongo:27017"
MONGODB_DB_NAME="chat-docs"
GEMINI_API_KEY="your-gemini-key"
ALLOWED_ORIGINS="http://localhost:3000"
```

> **Tip:** If you are running the provided Docker Compose file, the service names `postgres` and `mongo` resolve automatically inside the Docker network.

## API Usage Examples
Before calling protected endpoints, register and obtain an access token. Replace `TOKEN` with the JWT returned from the login endpoint.

### 1. Register a new user
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 2. Login and capture token
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 3. Upload a PDF
```bash
curl -X POST "http://localhost:8000/pdf-upload" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@/path/to/document.pdf"
```

### 4. List uploaded PDFs
```bash
curl -X GET "http://localhost:8000/pdf-list" \
  -H "Authorization: Bearer TOKEN"
```

### 5. Select a PDF for subsequent chats
```bash
curl -X POST "http://localhost:8000/pdf-select" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": "507f1f77bcf86cd799439011"
  }'
```

### 6. Parse PDF contents
```bash
curl -X POST "http://localhost:8000/pdf-parse" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": "507f1f77bcf86cd799439011"
  }'
```

### 7. Ask questions about the selected PDF
```bash
curl -X POST "http://localhost:8000/pdf-chat" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main points of this document?"
  }'
```

### 8. View chat history
```bash
curl -X GET "http://localhost:8000/chat-history" \
  -H "Authorization: Bearer TOKEN"
```

### 9. Health check
```bash
curl http://localhost:8000/health
```

## Testing

The project uses `pytest` for automated unit tests that cover authentication flows, PDF storage/parsing logic (with in-memory fakes), and key LLM utilities.

```bash
source .venv/bin/activate  # if you created a local virtualenv
pytest
```

To run a focused subset, provide a file path or keyword filter:

```bash
pytest tests/test_pdf_service.py -k parse
```

> **Note:** Tests run entirely offline—MongoDB GridFS is mocked and the relational database uses an in-memory SQLite engine.

## Known Issues & Limitations
- **Gemini dependency:** LLM-powered responses require a valid Gemini API key; without it, chat endpoints will fail.
- **PDF size cap:** Uploads are limited to 10 MB (`MAX_FILE_SIZE`) to avoid long parse times and memory spikes.
- **Minimal validation:** The PDF parsing pipeline assumes well-formed PDFs and does not handle corrupted files gracefully yet.
- **No rate limiting:** Currently lacks throttling or abuse prevention for API calls.
- **Migrations pending:** SQLAlchemy models rely on auto-created tables; Alembic migrations are not yet included.

## Future Improvements
- Add schema migrations via Alembic for safer database evolution.
- Implement request rate limiting and audit logging.
- Introduce background workers for large PDF processing.
- Expose a lightweight frontend for managing documents and viewing chats.

## Contributing
1. Fork the repository and create a feature branch.
2. Install development dependencies (`pytest`, `black`, `flake8`).
3. Run tests and linters before opening a pull request:
   ```bash
   pytest
   black .
   flake8
   ```
4. Submit a PR with a clear description of changes and testing evidence.

