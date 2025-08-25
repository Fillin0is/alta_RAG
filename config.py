from pathlib import Path


# Paths
MODEL_PATH = Path('models/Mistral-7B-Instruct-v0.3.Q5_K_S.gguf')
DATA_DIR = Path('documents')
FAISS_INDEX_DIR = Path('faiss_index')
MODEL_DIR = "./models/all-MiniLM-L6-v2"  # Модель эмбеддингов

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