from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
MODEL_PATH = os.getenv("MODEL_PATH", "models/Mistral-7B-Instruct-v0.3.Q5_K_S.gguf")
DOCX_PATH = os.getenv("DOCX_PATH", "data/docx_documents")
OBSIDIAN_PATH = os.getenv("OBSIDIAN_PATH", "data/obsidian_vault")
PDF_PATH = os.getenv("PDF_PATH", "data/pdf_documents")
EMBEDDING_PATH = os.getenv("EMBEDDING_PATH", "models/all-mpnet-base-v2")

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