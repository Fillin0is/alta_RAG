# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG (Retrieval-Augmented Generation) system for Alta-Soft company. Ingests documents (PDF, DOCX, Markdown), stores embeddings in PostgreSQL with pgvector, and provides intelligent responses via local LLM.

## Architecture

```
Frontend (Streamlit:8501) → API (FastAPI:8000) → PostgreSQL (pgvector:5432)
                                   ↓
                           Models (Embeddings + LLM)
```

**Three Docker services:**
- `postgres` — ankane/pgvector with vector search
- `api` — FastAPI backend with LLM inference
- `frontend` — Streamlit chat interface

## Commands

### Docker Compose (Production)
```bash
cd compose
docker-compose -f server.yml up -d      # Start all services
docker-compose -f server.yml down       # Stop all services
docker-compose -f server.yml logs -f    # View logs
```

### Local Development
```bash
# API
cd api && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && streamlit run app.py --server.port=8501

# Ingest documents
cd api && python ingest.py
```

### Database
```bash
./scripts/db_backup.sh                  # Backup database
./scripts/deploy.sh                     # Deploy/update system
```

## Key Files

| File | Purpose |
|------|---------|
| `api/main.py` | FastAPI endpoints: `/health`, `/generate` |
| `api/vector_store_pg.py` | PostgreSQL + pgvector wrapper, hybrid search |
| `api/llm_connector.py` | Mistral-7B inference via llama-cpp |
| `api/config.py` | Environment variables and defaults |
| `api/ingest.py` | Document ingestion orchestrator |
| `frontend/app.py` | Streamlit chat UI |
| `parsers/*.py` | Document format parsers (PDF, DOCX, MD) |
| `compose/server.yml` | Docker Compose configuration |

## Configuration

Environment variables (set in compose or .env):
```
DB_HOST=postgres  DB_PORT=5432  DB_NAME=rag_system_local
DB_USER=postgres  DB_PASSWORD=postgres
MODEL_PATH=models/Mistral-7B-Instruct-v0.3.Q5_K_S.gguf
EMBED_MODEL_PATH=models/multilingual-e5-large
N_GPU_LAYERS=0    # Set >0 for GPU acceleration
```

## Database Schema

```sql
-- files: tracks source documents with hash for deduplication
-- documents: chunks with embeddings (768-dim) and metadata
-- Indexes: IVFFlat for vector search, GIN for BM25
```

## Hybrid Search

`VectorStore.hybrid_search()` combines:
- Vector similarity (cosine distance) — semantic matching
- BM25 (ts_rank_cd) — keyword matching
- Alpha parameter controls weight (default 0.6 = 60% vector)

## Adding New Document Type

1. Create parser in `parsers/new_parser.py`
2. Import and call in `api/ingest.py`
3. Add path to `api/config.py`

## Notes

- UI and prompts are in Russian
- Embedding model: multilingual-e5-large (768 dimensions)
- LLM: Mistral-7B GGUF format (llama-cpp-python)
- Chunking: 700 chars with 200 char overlap
