"""LLM response caching.

Two options, switchable from the sidebar:

* InMemoryCache — lives in RAM, fastest, cleared when the app restarts.
* SQLiteCache   — a file on disk, survives restarts, shared across sessions.

`set_llm_cache()` registers ONE global cache; LangChain checks it before every
call, so an identical prompt returns instantly and costs nothing.

Note on the SQLite implementation: LangChain's own `SQLiteCache` lives in
`langchain-community`, which is being sunset. Rather than depend on a
deprecated package, this module implements the same thing directly on top of
`BaseCache` from `langchain-core` — about thirty lines, no extra dependency.
"""

from __future__ import annotations

import sqlite3
import threading
from typing import Any, Sequence

from langchain_core.caches import BaseCache, InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_core.load import dumps, loads

CACHE_DB_PATH = "codesage_cache.db"

CACHE_CHOICES = ["In-memory (fast, this session)", "SQLite (survives restarts)", "Off"]


class SQLiteCache(BaseCache):
    """A minimal, dependency-free SQLite cache for LLM responses."""

    def __init__(self, database_path: str = CACHE_DB_PATH) -> None:
        self.database_path = database_path
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    prompt     TEXT NOT NULL,
                    llm_string TEXT NOT NULL,
                    response   TEXT NOT NULL,
                    PRIMARY KEY (prompt, llm_string)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path, check_same_thread=False)

    def lookup(self, prompt: str, llm_string: str) -> Sequence[Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT response FROM llm_cache WHERE prompt = ? AND llm_string = ?",
                (prompt, llm_string),
            ).fetchone()
        if row is None:
            return None
        try:
            # `allowed_objects="core"` keeps deserialisation scoped to LangChain's
            # own core types — our cache file should never contain anything else.
            return loads(row[0], allowed_objects="core")
        except Exception:
            return None  # stale or unreadable entry — treat as a miss

    def update(self, prompt: str, llm_string: str, return_val: Sequence[Any]) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (prompt, llm_string, response) "
                "VALUES (?, ?, ?)",
                (prompt, llm_string, dumps(return_val)),
            )

    def clear(self, **kwargs: Any) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM llm_cache")


def configure_cache(choice: str) -> str:
    """Register the chosen global cache. Returns a short status string."""
    if choice.startswith("In-memory"):
        set_llm_cache(InMemoryCache())
        return "In-memory cache active"

    if choice.startswith("SQLite"):
        set_llm_cache(SQLiteCache(CACHE_DB_PATH))
        return f"SQLite cache active ({CACHE_DB_PATH})"

    set_llm_cache(None)
    return "Caching disabled"
