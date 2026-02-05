"""Database schema and init for SQLite"""

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Optional, Generator


SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User metrics configuration (which metrics each user has enabled)
CREATE TABLE IF NOT EXISTS user_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, metric_name)
);

-- Metric entries (actual data logged by users)
CREATE TABLE IF NOT EXISTS metric_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    value_type TEXT NOT NULL,  -- 'boolean', 'integer', 'decimal', 'text'
    value_boolean BOOLEAN,
    value_integer INTEGER,
    value_decimal REAL,
    value_text TEXT,
    metadata TEXT,  -- JSON string for additional data
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_metric_entries_user_metric
    ON metric_entries(user_id, metric_name);

CREATE INDEX IF NOT EXISTS idx_metric_entries_timestamp
    ON metric_entries(timestamp);

CREATE INDEX IF NOT EXISTS idx_metric_entries_user_timestamp
    ON metric_entries(user_id, timestamp);

-- Daily summary cache (LLM-generated summaries)
CREATE TABLE IF NOT EXISTS daily_summary_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    cache_date DATE NOT NULL,
    summary_content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, cache_date)
);
"""


class Database:
    """Database connection manager and init"""

    def __init__(self, db_path: Path) -> None:
        self.db_path: Path = db_path
        self._ensure_directory()
        self._initialized: bool = False

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Initialize the database schema if not already done"""
        if self._initialized:
            return
        with self.get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        self._initialized = True

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection]:
        """Context manager for database connection"""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute a query and return the results as a list of dictionaries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[dict]:
        """Execute a query and return a single result as a dictionary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_insert(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an insert query and return the last inserted ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
