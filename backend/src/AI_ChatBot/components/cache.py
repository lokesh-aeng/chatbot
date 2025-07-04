from time import time
from typing import Any, Dict, List, Optional, Tuple
import threading
import hashlib
import json
import os
import gzip
import sqlite3
from pathlib import Path
from datetime import datetime

from AI_ChatBot.entity import CacheConfig

def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _now_ts() -> float:
    return time()

def _is_expired(created_ts: float, ttl: int) -> bool:
    return (time() - created_ts) > ttl

class VectorCache:
    """In‑memory LRU cache for query embeddings."""
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.lock = threading.Lock()
        self.cache: Dict[str, Tuple[List[float], float]] = {}  # key → (vec, last_access_ts)
        self.order: List[str] = []

    def get(self, query: str) -> Optional[List[float]]:
        key = _hash_str(query)
        with self.lock:
            if key in self.cache:
                vec, _ = self.cache[key]
                # update recency
                self.cache[key] = (vec, _now_ts())
                self.order.remove(key)
                self.order.insert(0, key)
                return vec
        return None

    def set(self, query: str, vec: List[float]):
        key = _hash_str(query)
        with self.lock:
            if key in self.cache:
                # update existing
                self.order.remove(key)
            elif len(self.order) >= self.max_size:
                # evict LRU
                lru = self.order.pop()
                del self.cache[lru]
            # insert as most recent
            self.order.insert(0, key)
            self.cache[key] = (vec, _now_ts())

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.order.clear()

class QueryCache:
    """Persistent SQLite cache for raw query → metadata (e.g. stats, last used)."""
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_table()
        self.lock = threading.Lock()

    def _init_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS query_cache (
            query_hash TEXT PRIMARY KEY,
            query_text TEXT,
            last_used TIMESTAMP,
            use_count INTEGER DEFAULT 0
        )""")
        self.conn.commit()

    def touch(self, query: str):
        """Increment use_count & update last_used."""
        key = _hash_str(query)
        now = datetime.now().isoformat()
        with self.lock:
            cur = self.conn.execute(
                "SELECT use_count FROM query_cache WHERE query_hash = ?", (key,)
            )
            row = cur.fetchone()
            if row:
                count = row[0] + 1
                self.conn.execute(
                    "UPDATE query_cache SET use_count = ?, last_used = ? WHERE query_hash = ?",
                    (count, now, key)
                )
            else:
                self.conn.execute(
                    "INSERT INTO query_cache (query_hash, query_text, last_used, use_count) VALUES (?, ?, ?, 1)",
                    (key, query, now)
                )
            self.conn.commit()

    def get_stats(self, query: str) -> Optional[Dict[str, Any]]:
        key = _hash_str(query)
        cur = self.conn.execute(
            "SELECT query_text, last_used, use_count FROM query_cache WHERE query_hash = ?", (key,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"query_text": row[0], "last_used": row[1], "use_count": row[2]}

    def prune_lru(self, max_entries: int):
        """Evict oldest entries beyond `max_entries`."""
        with self.lock:
            cur = self.conn.execute(
                "SELECT query_hash FROM query_cache ORDER BY last_used ASC LIMIT -1 OFFSET ?;",
                (max_entries,)
            )
            keys = [r[0] for r in cur.fetchall()]
            for k in keys:
                self.conn.execute("DELETE FROM query_cache WHERE query_hash = ?", (k,))
            self.conn.commit()

    def clear(self):
        with self.lock:
            self.conn.execute("DELETE FROM query_cache")
            self.conn.commit()

class ResponseCache:
    """
    JSON‑file cache mapping (query + history hash) → response payload,
    with TTL, LRU eviction, size limit, manual invalidation.
    """
    def __init__(self,
                 cache_dir: Path ,
                 ttl_seconds: int,
                 max_total_bytes: int ):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl_seconds
        self.max_bytes = max_total_bytes
        self.lock = threading.Lock()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json.gz"

    def _enforce_size_limit(self):
        """Evict LRU files if total size > max_bytes."""
        files = list(self.cache_dir.glob("*.json.gz"))
        files.sort(key=lambda p: p.stat().st_atime)  # oldest access first
        total = sum(p.stat().st_size for p in files)
        for p in files:
            if total <= self.max_bytes:
                break
            size = p.stat().st_size
            p.unlink()
            total -= size

    def get(self, query: str, history: List[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        hist_serial = "|".join(f"{u}→{a}" for u, a in history)
        key = _hash_str(query)
        path = self._cache_path(key)
        if not path.exists():
            return None

        with self.lock:
            with gzip.open(path, "rt", encoding="utf-8") as fp:
                payload = json.load(fp)
            created = payload.get("_created_at", 0)
            if _is_expired(created, self.ttl):
                path.unlink()
                return None
            # update access time
            os.utime(path, None)
            return payload

    def set(self,
            query: str,
            history: List[Tuple[str, str]],
            response_payload: Dict[str, Any]):
        hist_serial = "|".join(f"{u}→{a}" for u, a in history)
        key = _hash_str(query)
        path = self._cache_path(key)
        payload = dict(response_payload)
        payload["_created_at"] = _now_ts()
        with self.lock:
            with gzip.open(path, "wt", encoding="utf-8") as fp:
                json.dump(payload, fp)
            self._enforce_size_limit()

    def invalidate(self, query: Optional[str] = None, history: Optional[List[Tuple[str, str]]] = None):
        """
        - If no args: clear full response cache.
        - If query only: delete all files whose key starts with hash(query).
        - If both: delete the exact (query,history) entry.
        """
        with self.lock:
            if query is None:
                # full wipe
                for p in self.cache_dir.glob("*.json.gz"):
                    p.unlink()
                return
            # specific
            hist_serial = "" if history is None else "|".join(f"{u}→{a}" for u, a in history)
            pattern = _hash_str(query + "||" + hist_serial)
            for p in self.cache_dir.glob(f"{pattern}*.json.gz"):
                p.unlink()

class CacheManager:
    """
    Combines VectorCache, QueryCache, and ResponseCache into one interface.
    """
    def __init__(self,config:CacheConfig):
        self.config = config
        self.vector_cache = VectorCache(max_size=self.config.vectors_max_size)
        self.query_cache = QueryCache(db_path=self.config.query_dir)
        self.response_cache = ResponseCache(
            cache_dir=self.config.json_dir,
            ttl_seconds=self.config.response_ttl,
            max_total_bytes=self.config.json_max_bytes
            )

    # — Vector caching —
    def get_vector(self, query: str) -> Optional[List[float]]:
        return self.vector_cache.get(query)

    def set_vector(self, query: str, vec: List[float]):
        return self.vector_cache.set(query, vec)

    # — Query metadata caching —
    def touch_query(self, query: str):
        return self.query_cache.touch(query)

    def get_query_stats(self, query: str):
        return self.query_cache.get_stats(query)

    # — Response caching —
    def get_response(self, query: str, history: List[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        return self.response_cache.get(query, history)

    def set_response(self,
                     query: str,
                     history: List[Tuple[str, str]],
                     response_text: str,
                     source_chunks: List[Dict[str, Any]],
                     model: str,
                     is_fallback: bool,
                     latency: float):
        payload = {
            "response_text": response_text,
            "source_chunks": source_chunks,
            "model": model,
            "is_fallback": is_fallback,
            "latency": latency
        }
        return self.response_cache.set(query, history, payload)

    def invalidate_response(self, query: Optional[str] = None, history: Optional[List[Tuple[str, str]]] = None):
        return self.response_cache.invalidate(query, history)

    # — Maintenance tasks —
    def prune_query_cache(self, max_entries: int):
        return self.query_cache.prune_lru(max_entries)

    def clear_all(self):
        self.vector_cache.clear()
        self.query_cache.clear()
        self.response_cache.invalidate()