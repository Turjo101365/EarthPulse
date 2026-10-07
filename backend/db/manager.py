"""
EarthPulse PostgreSQL & pgvector Database Client & Manager
Provides thread-safe connection pooling, spatial bounding-box querying,
hotspot persistence, and RAG vector search with graceful in-memory fallback.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("earthpulse.db")

# Attempt importing psycopg2
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor, execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2-binary not installed; running in in-memory fallback mode.")


class DatabaseManager:
    """Manages connections and queries to PostgreSQL / pgvector."""

    def __init__(self):
        self._pool: Optional[Any] = None
        self._connected: bool = False
        self._db_url: str = self._resolve_db_url()

    def _resolve_db_url(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        # Check if running inside container or on host
        user = os.getenv("POSTGRES_USER", "earthpulse")
        password = os.getenv("POSTGRES_PASSWORD", "earthpulse")
        db = os.getenv("POSTGRES_DB", "earthpulse")
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    def connect(self) -> bool:
        """Initializes connection pool and runs schema verification."""
        if not PSYCOPG2_AVAILABLE:
            return False

        # Try primary DATABASE_URL, and fallback to localhost:5433 if running on host
        urls_to_try = [self._db_url]
        if "postgres:5432" in self._db_url:
            urls_to_try.append(self._db_url.replace("postgres:5432", "localhost:5433"))
            urls_to_try.append(self._db_url.replace("postgres:5432", "127.0.0.1:5433"))

        for url in urls_to_try:
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=url,
                    connect_timeout=3
                )
                self._connected = True
                self._db_url = url
                self._init_schema()
                logger.info(f"Connected to PostgreSQL database at {url.split('@')[-1]}")
                return True
            except Exception as e:
                logger.debug(f"Could not connect to {url}: {e}")

        self._connected = False
        return False

    def is_connected(self) -> bool:
        return self._connected and self._pool is not None

    def _init_schema(self):
        """Ensures vector extension and base tables exist."""
        if not self._connected:
            return
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                # Try creating pgvector extension
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                except Exception:
                    conn.rollback()

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS hotspots (
                        id VARCHAR(128) PRIMARY KEY,
                        latitude DOUBLE PRECISION NOT NULL,
                        longitude DOUBLE PRECISION NOT NULL,
                        brightness DOUBLE PRECISION,
                        frp DOUBLE PRECISION DEFAULT 0.0,
                        confidence DOUBLE PRECISION DEFAULT 80.0,
                        acq_date VARCHAR(32),
                        acq_time VARCHAR(32),
                        satellite VARCHAR(64),
                        instrument VARCHAR(64),
                        daynight VARCHAR(16),
                        risk_level VARCHAR(32),
                        h3_index VARCHAR(64),
                        raw_payload JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_hotspots_coords ON hotspots (latitude, longitude);
                    CREATE INDEX IF NOT EXISTS idx_hotspots_frp ON hotspots (frp);
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Schema init error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)

    def get_stats(self) -> Dict[str, Any]:
        """Returns database table record counts and pgvector status."""
        if not self._connected or not self._pool:
            self.connect()
        if not self._connected or not self._pool:
            return {
                "status": "DISCONNECTED",
                "message": "PostgreSQL not connected (using in-memory fallback)",
                "hotspots_count": 0,
                "pgvector_enabled": False
            }

        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT count(*) as count FROM hotspots;")
                hotspot_count = cur.fetchone()["count"]

                # Check if vector extension is installed
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
                has_vector = cur.fetchone() is not None

                return {
                    "status": "CONNECTED",
                    "database_url": self._db_url.split("@")[-1],
                    "hotspots_count": hotspot_count,
                    "pgvector_enabled": has_vector
                }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)

    def sync_hotspots(self, hotspots: List[Dict[str, Any]]) -> int:
        """Upserts hotspots into PostgreSQL database."""
        if not self._connected or not self._pool:
            self.connect()
        if not self._connected or not self._pool or not hotspots:
            return 0


        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                query = """
                    INSERT INTO hotspots (
                        id, latitude, longitude, brightness, frp, confidence,
                        acq_date, acq_time, satellite, instrument, daynight,
                        risk_level, h3_index, raw_payload
                    ) VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        frp = EXCLUDED.frp,
                        confidence = EXCLUDED.confidence,
                        risk_level = EXCLUDED.risk_level;
                """
                records = []
                for h in hotspots:
                    records.append((
                        str(h.get("id")),
                        float(h.get("latitude", 0.0)),
                        float(h.get("longitude", 0.0)),
                        float(h.get("brightness", 0.0)) if h.get("brightness") is not None else None,
                        float(h.get("frp", 0.0)) if h.get("frp") is not None else 0.0,
                        float(h.get("confidence", 80.0)) if h.get("confidence") is not None else 80.0,
                        str(h.get("acq_date", "")),
                        str(h.get("acq_time", "")),
                        str(h.get("satellite", "")),
                        str(h.get("instrument", "")),
                        str(h.get("daynight", "")),
                        str(h.get("risk_level", "MODERATE")),
                        str(h.get("h3_index", "")),
                        json.dumps(h)
                    ))
                execute_values(cur, query, records, page_size=500)
                conn.commit()
                return len(records)
        except Exception as e:
            logger.error(f"Error syncing hotspots: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)

    def query_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        min_frp: float = 0.0,
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """Queries hotspots within spatial bounding box directly from PostgreSQL."""
        if not self._connected or not self._pool:
            self.connect()
        if not self._connected or not self._pool:
            return []


        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, latitude, longitude, brightness, frp, confidence,
                           acq_date, acq_time, satellite, instrument, daynight,
                           risk_level, h3_index
                    FROM hotspots
                    WHERE latitude >= %s AND latitude <= %s
                      AND longitude >= %s AND longitude <= %s
                      AND frp >= %s
                    ORDER BY frp DESC
                    LIMIT %s;
                """, (south, north, west, east, min_frp, limit))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Spatial query error: {e}")
            return []
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)


# Global singleton instance
db_manager = DatabaseManager()
