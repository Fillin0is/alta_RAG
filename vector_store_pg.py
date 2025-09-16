import psycopg2
from pgvector.psycopg2 import register_vector
from pgvector.vector import Vector
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
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
        self.model = SentenceTransformer(embed_path, device="cpu")
        self.conn = psycopg2.connect(**db_params)
        register_vector(self.conn)

        self._init_table()
        

    def _init_table(self):  
        """
        Создание таблицы для хранения данных при ее отсутствии
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(768) NOT NULL,
                    metadata JSONB NOT NULL,
                    content_hash TEXT UNIQUE,
                    uploaded_at TIMESTAMP
                );
                """
            )
        
        self.conn.commit()

    def _hash_content(self, text: str) -> str:
        """Вычисляем уникальный хэш для текста"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
        
    def create_index(self, texts: List[Dict]):
        """
        Сохраняем тексты и их эмбеддинги в PostgreSQL (таблица documents)
        Если документ с таким content уже существует - пропускаем.
        texts = [{"page_content": "...", "metadata": {...}}, ...]
        """
        if not texts:
            raise ValueError("Не переданы тексты для индексации")
        
        with self.conn.cursor() as cursor:
            for text in texts:
                content = text["page_content"]
                content_hash = self._hash_content(content)

                # Duplicate check
                cursor.execute(
                    f"""
                    SELECT 1 FROM documents WHERE content_hash = %s;
                    """, (content_hash,)
                )
                if cursor.fetchone():
                    continue

                embedding = self.model.encode(content).tolist()
                cursor.execute(
                    f'''
                    INSERT INTO documents (content, embedding, metadata, content_hash, uploaded_at)
                    VALUES (%s, %s, %s, %s, NOW());
                    ''', (content, Vector(embedding), Json(text["metadata"]), content_hash)
                )

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