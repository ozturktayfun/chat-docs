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

## 🔐 Authentication Flow

### Complete Workflow Example

```bash
#!/bin/bash

# 1. Register a new user
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpassword123"
  }')

echo "Registration Response: $REGISTER_RESPONSE"

# 2. Login to get JWT token
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpassword123"
  }')

# Extract token from response
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "JWT Token: $TOKEN"

# 3. Upload a PDF
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/pdf/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.pdf")

echo "Upload Response: $UPLOAD_RESPONSE"

# Extract PDF ID
PDF_ID=$(echo $UPLOAD_RESPONSE | jq -r '.pdf_id')

# 4. Select the PDF for chat
curl -s -X POST "http://localhost:8000/pdf/select" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"pdf_id\": \"$PDF_ID\"}"

# 5. Parse the PDF
curl -s -X POST "http://localhost:8000/pdf/parse" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"pdf_id\": \"$PDF_ID\"}"

# 6. Start chatting
curl -s -X POST "http://localhost:8000/chat/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please provide a brief summary of this document."
  }'
```

## 📋 Postman Collection

### Collection Structure
```json
{
  "info": {
    "name": "Document Chat Assistant API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Register User",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"password123\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/register",
              "host": ["{{baseUrl}}"],
              "path": ["auth", "register"]
            }
          }
        },
        {
          "name": "Login User",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"password123\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/login",
              "host": ["{{baseUrl}}"],
              "path": ["auth", "login"]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const response = pm.response.json();",
                  "    pm.collectionVariables.set('token', response.access_token);",
                  "}"
                ]
              }
            }
          ]
        }
      ]
    },
    {
      "name": "PDF Management",
      "item": [
        {
          "name": "Upload PDF",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{token}}"
              }
            ],
            "body": {
              "mode": "formdata",
              "formdata": [
                {
                  "key": "file",
                  "type": "file",
                  "src": "/path/to/sample.pdf"
                }
              ]
            },
            "url": {
              "raw": "{{baseUrl}}/pdf/upload",
              "host": ["{{baseUrl}}"],
              "path": ["pdf", "upload"]
            }
          }
        }
      ]
    }
  ]
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

## 🚨 Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "error": "Could not validate credentials",
  "status_code": 401
}
```

#### 400 Bad Request
```json
{
  "error": "Only PDF files are allowed",
  "status_code": 400
}
```

#### 404 Not Found
```json
{
  "error": "PDF not found",
  "status_code": 404
}
```

#### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "status_code": 500
}
```

## 🔍 Troubleshooting

### Common Issues

1. **"Could not validate credentials"**
   - Check if JWT token is included in Authorization header
   - Verify token format: `Bearer <token>`
   - Ensure token hasn't expired (30 minutes default)

2. **"PDF not found"**
   - Verify PDF was uploaded successfully
   - Check if PDF belongs to the authenticated user
   - Ensure PDF ID is correct

3. **"Failed to generate response from AI model"**
   - Verify Gemini API key is correct
   - Check if PDF was parsed before chatting
   - Ensure internet connection for API calls

4. **"Connection refused" errors**
   - Check if all Docker services are running
   - Verify database connections in docker-compose logs
   - Ensure ports are not conflicting with other services

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

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Keys**: Rotate API keys regularly
3. **HTTPS**: Use HTTPS in production environments
4. **Rate Limiting**: Implement rate limiting for production deployment
5. **Input Validation**: All inputs are validated server-side