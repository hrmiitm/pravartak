"""
database.py

Persistent SQLite storage for the AI Assistant.
"""

import sqlite3

DB_NAME = "assistant.db"


# ==========================================================
# Connection
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================================================
# Initialization
# ==========================================================

def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile (

            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# Save
# ==========================================================

def save_memory(key: str, value: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO profile(key, value)
        VALUES (?, ?)
        """,
        (key, value),
    )

    conn.commit()
    conn.close()


# ==========================================================
# Load
# ==========================================================

def load_memory(key: str):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT value
        FROM profile
        WHERE key = ?
        """,
        (key,),
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return None