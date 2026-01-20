import psycopg2
from pgvector.psycopg2 import register_vector
from pgvector.vector import Vector
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch

from typing import List, Dict
import hashlib


class VectorStore:
    def __init__(self, embed_path: str, db_params: Dict):
        """
        db_params = {
            "dbname": "...",
            "user": "...",
            "password": "...",
            "host": "...",
            "port": 5432
        }
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(embed_path, device=device)
        self.conn = psycopg2.connect(**db_params)
        self._init_table()
        register_vector(self.conn)

    def _init_table(self):  
        """
        Создание таблицы для хранения данных при ее отсутствии
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE EXTENSION IF NOT EXISTS vector;

                CREATE TABLE IF NOT EXISTS files (
                    id BIGSERIAL PRIMARY KEY,
                    source TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,
                    id_file BIGINT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    embedding vector(768) NOT NULL,
                    metadata JSONB NOT NULL
                );

                -- Индексы для ускорения поиска
                CREATE INDEX IF NOT EXISTS idx_documents_file ON documents(id_file);
                CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
                CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING gin (to_tsvector('simple', content));
                """
            )
        
        self.conn.commit()

    def _hash_content(self, text: str) -> str:
        """Вычисляем уникальный хэш для текста"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
        
    def create_index(self, texts: List[Dict], file_path: str):
        """
        texts = [{"page_content": "...", "metadata": {...}}, ...]
        file_path = путь к исходному файлу 

        Алгоритм:
        1. Считаем хэш файла
        2. Если файл уже есть в БД и хэш совпадает -> пропускаем
        3. Если файла нет или другой хэш:
            - удаляем старые чанки;
            - вставляем новые.
        """
        if not texts:
            raise ValueError("Не переданы тексты для индексации")
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, file_hash FROM files WHERE source = %s;
                """,
                (file_path,)
            )
            row = cursor.fetchone()

            if row and row[1] == file_hash:
                print(f"Файл {file_path} не был изменен")
                return
            
            if row:
                file_id = row[0]
                cursor.execute("DELETE FROM documents WHERE id_file = %s;", (file_id,))
                cursor.execute("DELETE FROM files WHERE id = %s;", (file_id,))
                print(f"♻️ {file_path} изменился, пересоздаём чанки")

            cursor.execute(
                """
                INSERT INTO files (source, file_hash, processed_at)
                VALUES (%s, %s, NOW())
                RETURNING id;
                """, 
                (file_path, file_hash)
            )
            file_id = cursor.fetchone()[0] # Сохраняем id новой записи файла

            for text in tqdm(texts, desc=f"Индексация {file_path}"):
                content = text["page_content"]
                embedding = self.model.encode(content).tolist()
                try:
                    cursor.execute(
                        """
                        INSERT INTO documents (id_file, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (file_id, content, Vector(embedding), Json(text["metadata"]))
                    )
                except Exception as e:
                    print(e)

        self.conn.commit()


    def hybrid_search(self, query: str, top_k=10, alpha=0.6) -> List[Dict]:
        """
        Гибридный поиск: BM25 + векторный поиск
        alpha = вес векторного скора (0..1)
        """
        query_embedding = self.model.encode(query).tolist()

        scores = {}

        with self.conn.cursor() as cursor:
            # Векторный поиск (top_k*2 кандидатов)
            cursor.execute(
                """
                SELECT id, content, metadata, 1 - (embedding <=> %s) AS vector_score
                FROM documents
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (Vector(query_embedding), Vector(query_embedding), top_k * 2),
            )
            vector_results = cursor.fetchall()

            if vector_results:
                max_v = max(r[3] for r in vector_results)
                min_v = min(r[3] for r in vector_results)
            else:
                max_v, min_v = 1, 0

            for doc_id, content, metadata, v_score in vector_results:
                norm_v = (v_score - min_v) / (max_v - min_v + 1e-9)
                scores[doc_id] = {"content": content, "metadata": metadata, "v_score": norm_v, "bm25": 0}

            # BM25 поиск (top_k*2 кандидатов)
            cursor.execute(
                """
                SELECT id, content, metadata,
                       ts_rank_cd(to_tsvector('simple', content), plainto_tsquery('simple', %s)) AS bm25_score
                FROM documents
                WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', %s)
                ORDER BY bm25_score DESC
                LIMIT %s;
                """,
                (query, query, top_k * 2),
            )
            bm25_results = cursor.fetchall()

            if bm25_results:
                max_b = max(r[3] for r in bm25_results)
                min_b = min(r[3] for r in bm25_results)
            else:
                max_b, min_b = 1, 0

            for doc_id, content, metadata, b_score in bm25_results:
                norm_b = (b_score - min_b) / (max_b - min_b + 1e-9)
                if doc_id in scores:
                    scores[doc_id]["bm25"] = norm_b
                else:
                    scores[doc_id] = {"content": content, "metadata": metadata, "v_score": 0, "bm25": norm_b}

        # Считаем финальный скор
        ranked = []
        for doc_id, vals in scores.items():
            final_score = alpha * vals["v_score"] + (1 - alpha) * vals["bm25"]
            ranked.append(
                {
                    "id": doc_id,
                    "page_content": vals["content"],
                    "metadata": vals["metadata"],
                    "score": final_score,
                }
            )

        ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)

        return ranked[:top_k]
