"""Lightweight database layer that replays local SQL dumps into SQLite."""
from __future__ import annotations

import re
import sqlite3
import codecs
from pathlib import Path
from threading import Lock
from typing import Iterable, List, Sequence, Tuple

TABLE_INSERT_LIMITS = {
    "dbo.alarm_history": 1000,
    "dbo.devices": 200,
    "dbo.sites_table": 200,
}
SCHEMA_PATTERN = re.compile(r"\b(?P<schema>dbo)\.(?P<table>[A-Za-z0-9_]+)", re.IGNORECASE)
INSERT_PATTERN = re.compile(r"\s*INSERT\s+INTO\s+\"?(?P<table>[^\"(]+)\"?", re.IGNORECASE)


class LocalSqlDatabase:
    """Loads exported ``.sql`` files into cached SQLite databases."""

    _init_lock = Lock()
    _query_lock = Lock()
    _connections: dict[Path, sqlite3.Connection] = {}

    def __init__(self, base_dir: Path | None = None, sql_files: Sequence[str] | None = None):
        self.base_dir = Path(base_dir or Path(__file__).parent / "sql_data")
        files = tuple(sql_files) if sql_files else self._discover_sql_files()
        if not files:
            raise FileNotFoundError(f"No .sql files found in {self.base_dir}")
        self.sql_files = tuple(f if f.endswith(".sql") else f"{f}.sql" for f in files)
        self.cache_path = self.base_dir / f".local_sql_cache_{self._cache_slug()}.db"
        self.conn = self._ensure_connection()

    def _cache_slug(self) -> str:
        return "_".join(Path(name).stem.replace(" ", "_") for name in self.sql_files)

    def _ensure_connection(self) -> sqlite3.Connection:
        if self.cache_path in self._connections:
            return self._connections[self.cache_path]
        with self._init_lock:
            if self.cache_path in self._connections:
                return self._connections[self.cache_path]
            needs_seed = self._cache_is_stale()
            if needs_seed and self.cache_path.exists():
                self.cache_path.unlink()
            conn = sqlite3.connect(self.cache_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            if needs_seed:
                self._seed_database(conn)
            self._connections[self.cache_path] = conn
            return conn

    def _cache_is_stale(self) -> bool:
        if not self.cache_path.exists():
            return True
        cache_mtime = self.cache_path.stat().st_mtime
        for filename in self._required_files():
            if filename.stat().st_mtime > cache_mtime:
                return True
        return False

    def _required_files(self) -> List[Path]:
        files: List[Path] = []
        for name in self.sql_files:
            path = self.base_dir / name
            if not path.exists():
                raise FileNotFoundError(f"Missing SQL dump: {path}")
            files.append(path)
        return files

    def _discover_sql_files(self) -> Tuple[str, ...]:
        files = sorted(p.name for p in self.base_dir.glob("*.sql"))
        return tuple(files)

    def _seed_database(self, conn: sqlite3.Connection) -> None:
        insert_counts: dict[str, int] = {}
        conn.execute("PRAGMA journal_mode=WAL;")
        for filename in self._required_files():
            self._load_script(conn, filename, insert_counts)
        conn.commit()

    def _iter_lines(self, path: Path):
        with path.open("rb") as raw:
            sample = raw.read(4)
            raw.seek(0)
            encoding = "utf-8"
            if sample.startswith(codecs.BOM_UTF16_LE):
                encoding = "utf-16-le"
            elif sample.startswith(codecs.BOM_UTF16_BE):
                encoding = "utf-16-be"
            elif sample.startswith(codecs.BOM_UTF8):
                encoding = "utf-8-sig"
        with path.open("r", encoding=encoding, errors="ignore") as handle:
            for line in handle:
                yield line

    def _load_script(
        self,
        conn: sqlite3.Connection,
        path: Path,
        insert_counts: dict[str, int],
    ) -> None:
        statement = ""
        for line in self._iter_lines(path):
            statement += line
            if sqlite3.complete_statement(statement):
                if not self._should_skip_insert(statement, insert_counts):
                    conn.execute(statement)
                statement = ""
        if statement.strip():
            if not self._should_skip_insert(statement, insert_counts):
                conn.execute(statement)

    def _should_skip_insert(self, statement: str, insert_counts: dict[str, int]) -> bool:
        match = INSERT_PATTERN.match(statement)
        if not match:
            return False
        table_name = match.group("table").strip().strip('"')
        limit = TABLE_INSERT_LIMITS.get(table_name)
        if limit is None:
            return True
        count = insert_counts.get(table_name, 0)
        if count >= limit:
            return True
        insert_counts[table_name] = count + 1
        return False

    def _normalize(self, sql: str) -> str:
        def repl(match: re.Match[str]) -> str:
            schema = match.group("schema")
            table = match.group("table")
            return f'"{schema}.{table}"'

        return SCHEMA_PATTERN.sub(repl, sql)

    def execute(self, sql: str, params: Iterable[object] | None = None) -> Tuple[Sequence[str], List[Tuple]]:
        normalized = self._normalize(sql)
        with self._query_lock:
            cur = self.conn.cursor()
            cur.execute(normalized, tuple(params or []))
            cols = tuple(col[0] for col in (cur.description or []))
            rows = [tuple(row) for row in cur.fetchall()]
        return cols, rows

    def query(self, sql: str, params: Iterable[object] | None = None) -> List[Tuple]:
        _, rows = self.execute(sql, params)
        return rows

    def query_with_columns(self, sql: str, params: Iterable[object] | None = None) -> Tuple[Sequence[str], List[Tuple]]:
        return self.execute(sql, params)

    def scalar(self, sql: str, params: Iterable[object] | None = None):
        rows = self.query(sql, params)
        return rows[0][0] if rows else None
