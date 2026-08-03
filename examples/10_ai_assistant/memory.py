"""
memory.py

Persistent memory using SQLite.
"""

from database import (
    save_memory,
    load_memory,
)


# ==========================================================
# Generic Memory
# ==========================================================

def remember(key: str, value: str):
    """
    Store a key-value pair in persistent memory.
    """
    save_memory(key, value)


def recall(key: str):
    """
    Retrieve a value from persistent memory.
    """
    return load_memory(key)


# ==========================================================
# Convenience Functions
# ==========================================================

def remember_name(name: str):
    remember("name", name)


def get_name():
    return recall("name")