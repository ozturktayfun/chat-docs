# API Usage Guide & Examples

## 🚀 Quick Start

### 1. Start the Application with Docker

```bash
# Clone the repository
git clone <your-repo-url>
cd mythai

# Copy environment variables
cp .env.example .env

# Edit .env file with your Gemini API key
# GEMINI_API_KEY=your-actual-api-key

# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f app
```

### 2. Access the API

- **API Base URL**: `http://localhost:8000`
- **Interactive Documentation**: `http://localhost:8000/docs`
- **Alternative Documentation**: `http://localhost:8000/redoc`

## 📡 API Endpoints

### Authentication Endpoints

#### Register New User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-10-03T10:30:00Z"
}
```

#### Login User
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### PDF Management Endpoints

#### Upload PDF File
```bash
curl -X POST "http://localhost:8000/pdf/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

**Response:**
```json
{
  "pdf_id": "507f1f77bcf86cd799439011",
  "filename": "document.pdf",
  "size": 1024000,
  "upload_date": "2025-10-03T10:35:00Z"
}
```

#### List User's PDFs
```bash
curl -X GET "http://localhost:8000/pdf/list" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
[
  {
    "pdf_id": "507f1f77bcf86cd799439011",
    "filename": "document.pdf",
    "upload_date": "2025-10-03T10:35:00Z",
    "is_parsed": false
  },
  {
    "pdf_id": "507f1f77bcf86cd799439012",
    "filename": "report.pdf",
    "upload_date": "2025-10-03T09:20:00Z",
    "is_parsed": true
  }
]
```

#### Select PDF for Chat
```bash
curl -X POST "http://localhost:8000/pdf/select" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": "507f1f77bcf86cd799439011"
  }'
```

**Response:**
```json
{
  "message": "PDF selected successfully",
  "pdf_id": "507f1f77bcf86cd799439011"
}
```

#### Parse PDF Text
```bash
curl -X POST "http://localhost:8000/pdf/parse" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_id": "507f1f77bcf86cd799439011"
  }'
```

**Response:**
```json
{
  "message": "PDF parsed successfully",
  "pdf_id": "507f1f77bcf86cd799439011",
  "page_count": 25,
  "text_length": 15420
}
```

### Chat Endpoints

#### Send Chat Message
```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main topics discussed in this document?"
  }'
```

**Response:**
```json
{
  "message": "What are the main topics discussed in this document?",
  "response": "Based on the document, the main topics discussed include: 1. Project architecture and system design, 2. Database configuration with PostgreSQL and MongoDB, 3. Authentication implementation using JWT tokens, 4. API endpoint specifications and examples...",
  "created_at": "2025-10-03T10:45:00Z"
}
```

#### Get Chat History
```bash
curl -X GET "http://localhost:8000/chat/history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "messages": [
    {
      "message": "What are the main topics discussed in this document?",
      "response": "Based on the document, the main topics discussed include...",
      "created_at": "2025-10-03T10:45:00Z"
    },
    {
      "message": "Can you summarize the key findings?",
      "response": "The key findings from the document are...",
      "created_at": "2025-10-03T10:50:00Z"
    }
  ],
  "total_count": 2
}
```

## 🔧 Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | `your-super-secret-key` |
| `POSTGRES_URL` | PostgreSQL connection URL | `postgresql://user:pass@localhost:5432/db` |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `GEMINI_API_KEY` | Google AI Studio API key | `AIza...` |

### Getting Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file


### Health Check

```bash
# Check application health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Logs

```bash
# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f postgres
docker-compose logs -f mongodb

# View all logs
docker-compose logs -f
```

## 📊 Performance Tips

1. **File Size**: Keep PDF files under 10MB for optimal performance
2. **Token Management**: Refresh JWT tokens before expiry
3. **Chunking**: Large documents are automatically chunked for better AI responses
4. **Concurrent Requests**: API supports concurrent requests with proper authentication

