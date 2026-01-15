from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).parent.parent

EMBED_MODEL_PATH = os.getenv("EMBED_MODEL_PATH", str(PROJECT_ROOT / "models/multilingual-e5-base"))
LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", str(PROJECT_ROOT / "models/Mistral-7B-Instruct-v0.3.Q8_0.gguf"))

DOCX_PATH = str(PROJECT_ROOT / "data/docx_documents")
OBSIDIAN_PATH = str(PROJECT_ROOT / "data/obsidian_vault")
PDF_PATH = str(PROJECT_ROOT / "data/pdf_documents")

# Model parameters
N_CTX = int(os.getenv("N_CTX", "4096"))
N_THREADS = int(os.getenv("N_THREADS", "10"))
N_BATCH = int(os.getenv("N_BATCH", "512"))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))

# Document parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# DB connection
DB_PARAMS = {
    "dbname": os.getenv("DB_NAME", "rag_system_local"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}