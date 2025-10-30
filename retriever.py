from pgvector.vector import Vector
from typing import List, Dict
from llm_connector import EmbedConnector


class AnswerSearch:
    def __init__(self, conn, embedder: EmbedConnector):
        """
        conn — psycopg2 соединение (из VectorStore)
        embedder — экземпляр EmbedConnector
        """
        self.conn = conn
        self.embedder = embedder

    def hybrid_search(self, query: str, top_k=10, alpha=0.6) -> List[Dict]:
        """
        Гибридный поиск: BM25 + векторный поиск через API-эмбеддер.
        alpha = вес векторного скора (0..1)
        """
        query_embedding = self.embedder.embed_text(query)

        scores = {}

        with self.conn.cursor() as cursor:
            # Векторный поиск
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

            # BM25 поиск
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