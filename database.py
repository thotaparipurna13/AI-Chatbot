import sqlite3
from datetime import datetime, timezone

from config import DATABASE_FILE


def get_connection():
    """Create a database connection with row access enabled."""
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the conversations and messages tables if they do not exist."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Conversation',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
            ON messages(conversation_id, created_at);
            """
        )
    return True


def create_conversation(title="New Conversation"):
    """Create a new conversation and return its ID."""
    timestamp = datetime.now(timezone.utc).isoformat()
    cleaned_title = (title or "New Conversation").strip() or "New Conversation"

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO conversations (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (cleaned_title, timestamp, timestamp),
        )
        return cursor.lastrowid


def add_message(conversation_id, role, content):
    """Insert a message into the given conversation."""
    if not conversation_id:
        raise ValueError("conversation_id is required")

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, role, content, timestamp),
        )
        connection.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (timestamp, conversation_id),
        )
    return True


def get_conversation_messages(conversation_id):
    """Return all messages for a conversation in order."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_conversations():
    """Return recent conversations with a preview from the latest user message."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.id,
                c.title,
                c.created_at,
                c.updated_at,
                (
                    SELECT m.content
                    FROM messages AS m
                    WHERE m.conversation_id = c.id AND m.role = 'user'
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS preview
            FROM conversations AS c
            ORDER BY c.updated_at DESC, c.id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def delete_conversation(conversation_id):
    """Delete a conversation and all of its messages."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        return cursor.rowcount > 0
