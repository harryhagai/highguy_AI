"""SQLite memory storage for Highguy AI Assistant."""

import sqlite3
from datetime import datetime
from pathlib import Path

try:
    from .config import DATABASE_PATH
except ImportError:
    from config import DATABASE_PATH


class MemoryManager:
    """Create, update, search, and delete local memories."""

    def __init__(self, db_path="highguy_ai.db"):
        if db_path == "highguy_ai.db":
            self.db_path = DATABASE_PATH
        else:
            self.db_path = Path(db_path)

        self.create_tables()

    def _connect(self):
        """Open a database connection and return rows like dictionaries."""
        try:
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as error:
            raise RuntimeError(f"Database connection failed: {error}") from error

    def create_tables(self):
        """Create the memory table automatically if it does not exist."""
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tags TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT
                    )
                    """
                )
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not create memory table: {error}") from error

    def add_memory(self, title, content, tags=""):
        """Save a new memory and return its database id."""
        title = title.strip()
        content = content.strip()
        tags = tags.strip()

        if not title or not content:
            raise ValueError("Title and content are required.")

        now = datetime.now().isoformat(timespec="seconds")

        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO memory (title, content, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (title, content, tags, now, now),
                )
                return cursor.lastrowid
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not save memory: {error}") from error

    def search_memory(self, keyword, limit=5):
        """Search memories by title, content, or tags."""
        keyword = keyword.strip()
        if not keyword:
            return []

        search_text = f"%{keyword}%"

        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, title, content, tags, created_at, updated_at
                    FROM memory
                    WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT ?
                    """,
                    (search_text, search_text, search_text, limit),
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not search memories: {error}") from error

    def get_all_memories(self):
        """Return every saved memory, newest first."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, title, content, tags, created_at, updated_at
                    FROM memory
                    ORDER BY created_at DESC
                    """
                ).fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not load memories: {error}") from error

    def delete_memory(self, memory_id):
        """Delete one memory by id. Returns True when a row was deleted."""
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM memory WHERE id = ?",
                    (memory_id,),
                )
                return cursor.rowcount > 0
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not delete memory: {error}") from error

    def update_memory(self, memory_id, title=None, content=None, tags=None):
        """Update selected fields for one memory."""
        updates = []
        values = []

        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("Title cannot be empty.")
            updates.append("title = ?")
            values.append(title)

        if content is not None:
            content = content.strip()
            if not content:
                raise ValueError("Content cannot be empty.")
            updates.append("content = ?")
            values.append(content)

        if tags is not None:
            updates.append("tags = ?")
            values.append(tags.strip())

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat(timespec="seconds"))
        values.append(memory_id)

        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    f"UPDATE memory SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
                return cursor.rowcount > 0
        except sqlite3.Error as error:
            raise RuntimeError(f"Could not update memory: {error}") from error
