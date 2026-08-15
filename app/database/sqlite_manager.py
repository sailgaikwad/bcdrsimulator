"""
SQLite database manager for the BCDR Simulator.

Handles connection lifecycle, schema initialization, and provides
a clean interface for the repository layer. SQLite is the authoritative
source of truth — the application MUST work without Google Cloud.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


# Path to schema.sql relative to this file
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Default database path
_DEFAULT_DB_DIR = Path(__file__).parent.parent.parent / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "bcdr_simulator.db"


class SQLiteManager:
    """
    Manages SQLite database connections and schema initialization.

    For in-memory databases (":memory:"), a single persistent connection is
    maintained because each sqlite3.connect(":memory:") call creates a
    completely separate empty database. For file-based databases, connections
    are created on demand.

    Usage:
        db = SQLiteManager()          # uses default path
        db = SQLiteManager(":memory:")  # in-memory for testing
        db.initialize()

        with db.connection() as conn:
            conn.execute("SELECT ...")
    """

    def __init__(self, db_path: str | None = None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
                     Use ":memory:" for in-memory databases (testing).
                     Defaults to data/bcdr_simulator.db relative to project root.
        """
        if db_path is None:
            # Use environment variable or default
            db_path = os.environ.get("BCDR_DB_PATH", str(_DEFAULT_DB_PATH))

        self.db_path = db_path
        self._is_memory = (db_path == ":memory:")
        self._persistent_conn: sqlite3.Connection | None = None
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Create the database directory if it doesn't exist."""
        if not self._is_memory:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """Apply standard connection settings."""
        conn.row_factory = sqlite3.Row  # Dict-like row access
        if not self._is_memory:
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read perf
        conn.execute("PRAGMA foreign_keys=ON")    # Enforce referential integrity

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.

        For in-memory databases, returns the single persistent connection.
        For file databases, creates a new connection each time.
        """
        if self._is_memory:
            if self._persistent_conn is None:
                self._persistent_conn = sqlite3.connect(":memory:")
                self._configure_connection(self._persistent_conn)
            return self._persistent_conn
        else:
            conn = sqlite3.connect(self.db_path)
            self._configure_connection(conn)
            return conn

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.

        Automatically commits on success, rolls back on exception.
        For in-memory databases, the connection is NOT closed (persistent).
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Only close file-based connections; keep in-memory alive
            if not self._is_memory:
                conn.close()

    def initialize(self) -> None:
        """
        Initialize the database schema from schema.sql.

        Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS.
        """
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        with self.connection() as conn:
            conn.executescript(schema_sql)

    def reset(self) -> None:
        """
        Drop all tables and reinitialize. USE ONLY FOR TESTING.
        """
        with self.connection() as conn:
            # Get all table names
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table['name']}")
        self.initialize()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        with self.connection() as conn:
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            ).fetchone()
            return result is not None

    def get_table_count(self, table_name: str) -> int:
        """Get the row count of a table."""
        with self.connection() as conn:
            result = conn.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()
            return result["cnt"]

    def close(self) -> None:
        """Close the persistent connection (for in-memory databases)."""
        if self._persistent_conn is not None:
            self._persistent_conn.close()
            self._persistent_conn = None
