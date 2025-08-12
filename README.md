# RAG Knowledge Base Service

A FastAPI-based Retrieval-Augmented Generation (RAG) service for managing and searching knowledge bases using vector embeddings and ChromaDB.

## 🌟 Features

- **Document Processing**: Upload and process DOCX files to create searchable knowledge bases
- **Vector Search**: Semantic search using OpenAI embeddings and ChromaDB vector database
- **Authentication**: Built-in credential verification system
- **Metrics Tracking**: Monitor and track KB performance metrics with drift detection
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Chunking Strategy**: Intelligent document chunking for optimal retrieval

## 🏗️ Architecture

```
rag_kb_service/
├── app/
│   ├── __init__.py
│   ├── auth.py              # Authentication and credential verification
│   ├── chunker.py           # Document chunking logic
│   ├── config.py            # Configuration management
│   ├── kb_manager.py        # Knowledge base operations
│   ├── main.py              # FastAPI application and routes
│   ├── manifest_store.py    # Metrics and manifest storage
│   ├── utils.py            # Utility functions
│   └── models/             # Data models
├── scripts/
│   └── backfill_metrics.py # Metrics backfill script
├── chroma_store/           # ChromaDB vector database
├── kb_catalog.db          # SQLite database for metadata
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/siva10x/rag_kb_service.git
   cd rag_kb_service
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the service**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Authentication
API_USERNAME=your_username
API_PASSWORD=your_password

# Database Configuration
CHROMA_DB_PATH=./chroma_store
MANIFEST_DB_PATH=./kb_catalog.db

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
LOG_LEVEL=INFO
```

## 📚 API Endpoints

### Health Check
```http
GET /kb/status
```
Check if the KB service is running.

### Initialize Knowledge Base
```http
POST /kb/init
```
Upload a DOCX file to initialize a new knowledge base.

**Parameters:**
- `file`: DOCX file (multipart/form-data)
- `index_version`: Optional version identifier
- Authentication required

### Add to Knowledge Base
```http
POST /kb/add
```
Add documents to an existing knowledge base (incremental).

**Parameters:**
- `file`: DOCX file (multipart/form-data)
- `index_version`: Optional version identifier
- Authentication required

### Search Knowledge Base
```http
POST /kb/search_test
```
Search the knowledge base with a query.

**Parameters:**
- `query`: Search query string
- Authentication required

### Metrics Endpoints
```http
POST /metrics/log
GET /metrics/drift-check
```
Monitor and log performance metrics with drift detection.

## 🔍 Usage Examples

### Initialize a Knowledge Base

```bash
curl -X POST "http://localhost:8000/kb/init" \
  -H "Authorization: Basic $(echo -n 'username:password' | base64)" \
  -F "file=@your_document.docx" \
  -F "index_version=v1.0"
```

### Search the Knowledge Base

```bash
curl -X POST "http://localhost:8000/kb/search_test" \
  -H "Authorization: Basic $(echo -n 'username:password' | base64)" \
  -F "query=What is the return policy?"
```

## 🛠️ Development

### Project Structure

- **`app/main.py`**: FastAPI application with route definitions
- **`app/kb_manager.py`**: Core knowledge base operations
- **`app/chunker.py`**: Document chunking and preprocessing
- **`app/auth.py`**: Authentication middleware
- **`app/manifest_store.py`**: Metrics and metadata storage
- **`scripts/`**: Utility scripts for maintenance




## 🔒 Security

- Basic authentication for API endpoints
- Environment variable-based configuration

## 📊 Monitoring

The service includes built-in metrics tracking:

- **Drift Detection**: Monitor embedding drift over time
- **Performance Metrics**: Track search latency and accuracy
- **Usage Analytics**: Log query patterns and frequency

Run the metrics backfill script:
```bash
python scripts/backfill_metrics.py
```

## 🐳 Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **ChromaDB Connection Error**
   - Ensure the `chroma_store/` directory exists
   - Check file permissions

2. **OpenAI API Errors**
   - Verify your API key is valid
   - Check rate limits and billing

3. **Authentication Failures**
   - Verify credentials in `.env` file
   - Check base64 encoding for Basic auth



**Built with ❤️ using FastAPI, ChromaDB, and OpenAI**