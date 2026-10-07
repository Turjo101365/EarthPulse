"""
PostgreSQL + pgvector Database Service for EarthPulse
Manages vector document storage, HNSW cosine index, and session chat persistence.
Provides automatic graceful fallback to SQLite/memory if PostgreSQL is unreachable.
"""

import os
import json
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger("earthpulse.db")

try:
    import psycopg
    from pgvector.psycopg import register_vector
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False
    logger.warning("psycopg or pgvector library not found; running in fallback mode.")


class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://earthpulse:earthpulse@localhost:5433/earthpulse"
        )
        self.has_pg = False
        self.vector_enabled = False
        self.fallback_db_path = Path(__file__).resolve().parent.parent.parent / "data" / "earthpulse_fallback.db"
        self._init_storage()

    def _get_connection(self):
        """Returns a psycopg connection if available."""
        if not HAS_PSYCOPG:
            return None
        try:
            conn = psycopg.connect(self.db_url, connect_timeout=4)
            return conn
        except Exception as e:
            logger.debug(f"PostgreSQL connection to {self.db_url} failed: {e}")
            return None

    def _init_storage(self):
        """Initializes PostgreSQL schema and vector extension; falls back to SQLite if needed."""
        self.fallback_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Try PostgreSQL
        conn = self._get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Enable vector extension
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                    if cur.fetchone():
                        self.vector_enabled = True
                    
                    # Create documents table with vector(1536)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            id VARCHAR(128) PRIMARY KEY,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            source TEXT NOT NULL,
                            category VARCHAR(64) NOT NULL,
                            dataset VARCHAR(64),
                            satellite VARCHAR(64),
                            metadata JSONB DEFAULT '{}'::jsonb,
                            embedding vector(1536),
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        );
                    """)

                    # Create HNSW vector index for cosine distance
                    try:
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx 
                            ON documents USING hnsw (embedding vector_cosine_ops);
                        """)
                    except Exception as idx_err:
                        logger.warning(f"HNSW index creation notice: {idx_err}")

                    # Create conversation tables
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id VARCHAR(64) PRIMARY KEY,
                            title TEXT,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ DEFAULT NOW()
                        );
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id SERIAL PRIMARY KEY,
                            conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE CASCADE,
                            role VARCHAR(20) NOT NULL,
                            content TEXT NOT NULL,
                            sources JSONB DEFAULT '[]'::jsonb,
                            intent VARCHAR(32),
                            metadata JSONB DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        );
                    """)
                conn.commit()
                self.has_pg = True
                logger.info("✅ PostgreSQL + pgvector connected and schema initialized successfully.")
            except Exception as e:
                logger.error(f"PostgreSQL schema initialization error: {e}")
                self.has_pg = False
            finally:
                conn.close()

        # 2. Always ensure fallback SQLite schema is ready
        self._init_sqlite_fallback()

    def _init_sqlite_fallback(self):
        """Initializes fallback SQLite database for resilient vector storage and chat history."""
        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("""
                    CREATE TABLE IF NOT EXISTS fallback_documents (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        source TEXT,
                        category TEXT,
                        dataset TEXT,
                        satellite TEXT,
                        metadata TEXT,
                        embedding TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                scur.execute("""
                    CREATE TABLE IF NOT EXISTS fallback_conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                scur.execute("""
                    CREATE TABLE IF NOT EXISTS fallback_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT,
                        role TEXT,
                        content TEXT,
                        sources TEXT,
                        intent TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                sconn.commit()
        except Exception as e:
            logger.error(f"SQLite fallback initialization failed: {e}")

    def upsert_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        source: str,
        category: str,
        dataset: Optional[str] = None,
        satellite: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Upserts a document and its embedding vector into PostgreSQL (and fallback SQLite)."""
        meta_dict = metadata or {}
        embedding_list = embedding or [0.0] * 1536
        
        # 1. Write to PostgreSQL if active
        if self.has_pg and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    register_vector(conn)
                    with conn.cursor() as cur:
                        emb_arr = np.array(embedding_list, dtype=np.float32)
                        cur.execute("""
                            INSERT INTO documents (
                                id, title, content, source, category, dataset, satellite, metadata, embedding, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (id) DO UPDATE SET
                                title = EXCLUDED.title,
                                content = EXCLUDED.content,
                                source = EXCLUDED.source,
                                category = EXCLUDED.category,
                                dataset = EXCLUDED.dataset,
                                satellite = EXCLUDED.satellite,
                                metadata = EXCLUDED.metadata,
                                embedding = EXCLUDED.embedding,
                                created_at = NOW();
                        """, (
                            doc_id, title, content, source, category, dataset, satellite,
                            json.dumps(meta_dict), emb_arr
                        ))
                    conn.commit()
                except Exception as e:
                    logger.error(f"PostgreSQL upsert_document failed ({e}); recording in fallback store.")
                finally:
                    conn.close()

        # 2. Mirror into fallback SQLite for 100% offline reliability
        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("""
                    INSERT OR REPLACE INTO fallback_documents (
                        id, title, content, source, category, dataset, satellite, metadata, embedding
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, title, content, source, category, dataset, satellite,
                    json.dumps(meta_dict), json.dumps(embedding_list)
                ))
                sconn.commit()
            return True
        except Exception as e:
            logger.error(f"SQLite fallback upsert failed: {e}")
            return False

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_category: Optional[str] = None,
        filter_dataset: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes vector cosine similarity search in PostgreSQL via pgvector <=> operator.
        Falls back to in-memory cosine ranking over SQLite if PostgreSQL is unreachable.
        """
        if self.has_pg and self.vector_enabled and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    register_vector(conn)
                    with conn.cursor() as cur:
                        q_arr = np.array(query_embedding, dtype=np.float32)
                        
                        where_clauses = []
                        params: List[Any] = [q_arr]

                        if filter_category:
                            where_clauses.append("category = %s")
                            params.append(filter_category)
                        if filter_dataset:
                            where_clauses.append("dataset ILIKE %s")
                            params.append(f"%{filter_dataset}%")

                        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                        params.extend([q_arr, top_k])

                        # embedding <=> q_arr calculates cosine distance (0=identical, 2=opposite)
                        sql = f"""
                            SELECT 
                                id, title, content, source, category, dataset, satellite, metadata,
                                1.0 - (embedding <=> %s) AS relevance_score
                            FROM documents
                            {where_sql}
                            ORDER BY embedding <=> %s ASC
                            LIMIT %s;
                        """
                        cur.execute(sql, params)
                        rows = cur.fetchall()

                        results = []
                        for r in rows:
                            meta = r[7] if isinstance(r[7], dict) else json.loads(r[7] or "{}")
                            score = max(0.0, min(1.0, float(r[8]) if r[8] is not None else 0.0))
                            results.append({
                                "id": r[0],
                                "title": r[1],
                                "content": r[2],
                                "source": r[3],
                                "category": r[4],
                                "dataset": r[5],
                                "satellite": r[6],
                                "metadata": meta,
                                "relevance": round(score, 3)
                            })
                        if results:
                            return results
                except Exception as e:
                    logger.warning(f"PostgreSQL vector search failed ({e}); using fallback search.")
                finally:
                    conn.close()

        # Fallback in-memory cosine search over SQLite cache
        return self._fallback_similarity_search(query_embedding, top_k, filter_category, filter_dataset)

    def _fallback_similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_category: Optional[str] = None,
        filter_dataset: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculates cosine similarity in Python over stored document vectors."""
        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("SELECT id, title, content, source, category, dataset, satellite, metadata, embedding FROM fallback_documents")
                rows = scur.fetchall()
                if not rows:
                    return []

                q_vec = np.array(query_embedding, dtype=np.float32)
                q_norm = np.linalg.norm(q_vec) or 1e-9

                scored = []
                for r in rows:
                    cat = r[4]
                    dset = r[5] or ""
                    if filter_category and cat != filter_category:
                        continue
                    if filter_dataset and filter_dataset.lower() not in dset.lower():
                        continue

                    emb_list = json.loads(r[8] or "[]")
                    if not emb_list:
                        continue
                    doc_vec = np.array(emb_list, dtype=np.float32)
                    doc_norm = np.linalg.norm(doc_vec) or 1e-9
                    cos_sim = float(np.dot(q_vec, doc_vec) / (q_norm * doc_norm))
                    score = round(max(0.0, min(1.0, (cos_sim + 1.0) / 2.0)), 3)

                    meta = json.loads(r[7] or "{}")
                    scored.append({
                        "id": r[0],
                        "title": r[1],
                        "content": r[2],
                        "source": r[3],
                        "category": r[4],
                        "dataset": r[5],
                        "satellite": r[6],
                        "metadata": meta,
                        "relevance": score
                    })

                scored.sort(key=lambda x: x["relevance"], reverse=True)
                return scored[:top_k]
        except Exception as e:
            logger.error(f"Fallback similarity search error: {e}")
            return []

    def get_document_count(self) -> int:
        """Returns total documents stored in PostgreSQL (or fallback)."""
        if self.has_pg and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM documents;")
                        res = cur.fetchone()
                        return res[0] if res else 0
                except Exception:
                    pass
                finally:
                    conn.close()

        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("SELECT COUNT(*) FROM fallback_documents;")
                res = scur.fetchone()
                return res[0] if res else 0
        except Exception:
            return 0

    def save_chat_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        intent: Optional[str] = "rag",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Saves a user or assistant message to database history."""
        sources_json = json.dumps(sources or [])
        meta_json = json.dumps(metadata or {})

        if self.has_pg and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO conversations (id, updated_at)
                            VALUES (%s, NOW())
                            ON CONFLICT (id) DO UPDATE SET updated_at = NOW();
                        """, (conversation_id,))
                        cur.execute("""
                            INSERT INTO chat_messages (conversation_id, role, content, sources, intent, metadata, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW());
                        """, (conversation_id, role, content, sources_json, intent, meta_json))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"PostgreSQL save_chat_message notice: {e}")
                finally:
                    conn.close()

        # Mirror in fallback SQLite
        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("""
                    INSERT OR REPLACE INTO fallback_conversations (id, updated_at)
                    VALUES (?, CURRENT_TIMESTAMP)
                """, (conversation_id,))
                scur.execute("""
                    INSERT INTO fallback_messages (conversation_id, role, content, sources, intent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (conversation_id, role, content, sources_json, intent, meta_json))
                sconn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed saving chat message: {e}")
            return False

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves chronological conversation history for session grounding."""
        if self.has_pg and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT role, content, sources, intent, metadata, created_at
                            FROM chat_messages
                            WHERE conversation_id = %s
                            ORDER BY id ASC
                            LIMIT %s;
                        """, (conversation_id, limit))
                        rows = cur.fetchall()
                        messages = []
                        for r in rows:
                            src = r[2] if isinstance(r[2], list) else json.loads(r[2] or "[]")
                            meta = r[4] if isinstance(r[4], dict) else json.loads(r[4] or "{}")
                            messages.append({
                                "role": r[0],
                                "content": r[1],
                                "sources": src,
                                "intent": r[3],
                                "metadata": meta
                            })
                        if messages:
                            return messages
                except Exception as e:
                    logger.debug(f"PostgreSQL get_conversation_history notice: {e}")
                finally:
                    conn.close()

        # Fallback from SQLite
        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("""
                    SELECT role, content, sources, intent, metadata
                    FROM fallback_messages
                    WHERE conversation_id = ?
                    ORDER BY id ASC
                    LIMIT ?
                """, (conversation_id, limit))
                rows = scur.fetchall()
                messages = []
                for r in rows:
                    messages.append({
                        "role": r[0],
                        "content": r[1],
                        "sources": json.loads(r[2] or "[]"),
                        "intent": r[3],
                        "metadata": json.loads(r[4] or "{}")
                    })
                return messages
        except Exception as e:
            logger.error(f"Fallback history fetch failed: {e}")
            return []

    def clear_conversation_history(self, conversation_id: str) -> bool:
        """Deletes chat messages for a conversation session."""
        if self.has_pg and HAS_PSYCOPG:
            conn = self._get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM chat_messages WHERE conversation_id = %s;", (conversation_id,))
                        cur.execute("DELETE FROM conversations WHERE id = %s;", (conversation_id,))
                    conn.commit()
                except Exception:
                    pass
                finally:
                    conn.close()

        try:
            with sqlite3.connect(self.fallback_db_path) as sconn:
                scur = sconn.cursor()
                scur.execute("DELETE FROM fallback_messages WHERE conversation_id = ?", (conversation_id,))
                scur.execute("DELETE FROM fallback_conversations WHERE id = ?", (conversation_id,))
                sconn.commit()
            return True
        except Exception:
            return False


# Global database manager singleton
db_manager = DatabaseManager()
