import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/rag_db"
)

# Normalize postgresql:// to postgresql+psycopg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Strip schema query param if present
if "?schema=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?schema=")[0]

# --- File Storage ---
STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# --- Text Chunking ---
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

# --- Embedding Model ---
# all-MiniLM-L6-v2: 384-dimensional, Apache-2.0, runs locally via
# sentence-transformers after its first download to the local model cache.
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

# --- ChromaDB ---
CHROMA_PERSIST_DIRECTORY: str = os.getenv(
    "CHROMA_PERSIST_DIRECTORY",
    os.path.join(os.path.dirname(__file__), "chroma_data")
)
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "document_chunks")

# --- Retrieval / RAG ---
TOP_K: int = int(os.getenv("TOP_K", "4"))
# ChromaDB cosine distance is converted to similarity as ``1 - distance``.
# Only chunks meeting this minimum similarity are used as LLM context.
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))
MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "6000"))

if TOP_K < 1:
    raise ValueError("TOP_K must be at least 1.")
if not -1.0 <= SIMILARITY_THRESHOLD <= 1.0:
    raise ValueError("SIMILARITY_THRESHOLD must be between -1 and 1.")
if MAX_CONTEXT_LENGTH < 1:
    raise ValueError("MAX_CONTEXT_LENGTH must be at least 1.")

# --- LLM ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
