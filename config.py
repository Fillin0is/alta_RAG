from pathlib import Path


# Paths
MODEL_PATH = "models/Mistral-7B-Instruct-v0.3.Q5_K_S.gguf"
DOCX_PATH = "data/documents"
EMBEDDING_PATH = "models/all-mpnet-base-v2"  # Модель эмбеддингов
OBSIDIAN_PATH = "data/obsidian_vault"

# Model parameters
N_CTX = 8192
N_TREADS = 6
N_GPU_LAYERS = 35

# Document parameters
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# DB connection
DB_PARAMS = {
            "dbname": "rag_system",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": 5432
        }