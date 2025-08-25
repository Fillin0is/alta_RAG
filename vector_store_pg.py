import psycopg2
from pgvector.psycopg2 import register_vector
from pgvector.vector import Vector
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import hashlib


class VectorStore:
    def __init__(self, model_path: str, db_params: Dict):
        """
        db_params = {
            "dbname": "...",
            "user": "...",
            "password": "...",
            "host": "...",
            "port": 5432
        }
        """
        self.model = SentenceTransformer(model_path, device="cpu")
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
                    embedding vector(384) NOT NULL,
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
            
    
    def similarity_search(self, query: str, k: int = 3) -> List[Dict]:
        """
        Поиск похожих документов по вектору запроса
        """
        query_embedding = self.model.encode(query).tolist()
        
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT content, embedding <-> %s AS distance
                FROM documents
                ORDER BY distance
                LIMIT %s;
                """, (Vector(query_embedding), k)
            )
            rows = cursor.fetchall()
            return [{"page_content": row[0], "distance": row[1]} for row in rows]