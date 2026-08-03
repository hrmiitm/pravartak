"""
database.py

SQLite database for persistent memory.
"""

import sqlite3

DB_NAME = "assistant.db"


def get_connection():
    """
    Create a SQLite connection.
    """
    return sqlite3.connect(DB_NAME)


def initialize_database():
    """
    Create required tables.
    """

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