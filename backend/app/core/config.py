import os
from dotenv import load_dotenv

load_dotenv()

# --- System / Environment ---
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# CORS configuration (comma-separated origins)
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
)
ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

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
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
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
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")
)
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "document_chunks")

# --- Retrieval / RAG ---
TOP_K: int = int(os.getenv("TOP_K", "4"))
# ChromaDB cosine distance is converted to similarity as ``1 - distance``.
# Only chunks meeting this minimum similarity are used as LLM context.
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))
MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "6000"))
CHAT_HISTORY_MESSAGE_LIMIT: int = int(os.getenv("CHAT_HISTORY_MESSAGE_LIMIT", "10"))

# --- Evaluation ---
EVAL_TOP_K: int = int(os.getenv("EVAL_TOP_K", str(TOP_K)))
EVAL_DATASET_PATH: str = os.getenv(
    "EVAL_DATASET_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "dataset.json")
)
EVAL_OUTPUT_PATH: str = os.getenv(
    "EVAL_OUTPUT_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "reports", "latest_report.json")
)
EVAL_USE_LLM_JUDGE: bool = os.getenv("EVAL_USE_LLM_JUDGE", "false").lower() in ("true", "1", "yes")
EVAL_LLM_JUDGE_MODEL: str = os.getenv("EVAL_LLM_JUDGE_MODEL", "llama-3.3-70b-versatile")

if TOP_K < 1:
    raise ValueError("TOP_K must be at least 1.")
if not -1.0 <= SIMILARITY_THRESHOLD <= 1.0:
    raise ValueError("SIMILARITY_THRESHOLD must be between -1 and 1.")
if MAX_CONTEXT_LENGTH < 1:
    raise ValueError("MAX_CONTEXT_LENGTH must be at least 1.")
if CHAT_HISTORY_MESSAGE_LIMIT < 1:
    raise ValueError("CHAT_HISTORY_MESSAGE_LIMIT must be at least 1.")
if EVAL_TOP_K < 1:
    raise ValueError("EVAL_TOP_K must be at least 1.")

# --- LLM ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
# Default Groq model: llama-3.3-70b-versatile (fast, capable, free tier available)
# Other options: llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")

# --- Authentication ---
JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 1.")
