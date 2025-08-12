import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
KB_COLLECTION_NAME = os.getenv("KB_COLLECTION_NAME", "trendora_kb")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./kb_catalog.db")
API_USERNAME = os.getenv("API_USERNAME", "demo_user")
API_PASSWORD = os.getenv("API_PASSWORD", "demo_pass")
BATCH_SIZE_EMBEDDINGS = int(os.getenv("BATCH_SIZE_EMBEDDINGS", "100"))
