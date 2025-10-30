import psycopg2
from pgvector.psycopg2 import register_vector
from pgvector.vector import Vector
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from llm_connector import EmbedConnector
from typing import List, Dict
from tqdm import tqdm
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
        self.model = EmbedConnector()
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
                CREATE TABLE IF NOT EXISTS files (
                    id BIGSERIAL PRIMARY KEY,
                    source TEXT UNIQUE NOT NULL,       -- путь или имя файла
                    file_hash TEXT NOT NULL,           -- sha256 файла
                    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,
                    id_file BIGINT NOT NULL REFERENCES files(id) ON DELETE CASCADE, -- связь с файлом
                    content TEXT NOT NULL,
                    embedding vector(1536) NOT NULL,
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
        
        # 1. Считаем хэш файла
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        with self.conn.cursor() as cursor:
            # 2. Проверяем, есть ли уже такой файл
            cursor.execute(
                "SELECT id, file_hash FROM files WHERE source = %s;",
                (file_path,)
            )
            row = cursor.fetchone()

            if row and row[1] == file_hash:
                print(f"✅ Файл {file_path} не был изменен, пропуск")
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
            file_id = cursor.fetchone()[0]

            contents = [t["page_content"] for t in texts]

            all_embeddings = []
            batch_size = 100
            for i in range(0, len(contents), batch_size):
                batch = contents[i:i + batch_size]
                batch_embeddings = self.model.embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

            try:
                for text, embedding in zip(texts, all_embeddings):
                    cursor.execute(
                        """
                        INSERT INTO documents (id_file, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (file_id, text["page_content"], Vector(embedding), Json(text["metadata"]))
                    )
            except Exception as e:
                print(f"Ошибка {e}")

        print(f"📄 Файл {file_path} успешно проиндексирован ({len(texts)} чанков)")

        self.conn.commit()