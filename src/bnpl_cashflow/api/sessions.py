"""Bounded, expiring in-memory workspaces for the public demo."""

from contextlib import contextmanager
from dataclasses import dataclass, field
import secrets
import sqlite3
from threading import Lock
from time import monotonic
from uuid import uuid4

from fastapi import HTTPException

from bnpl_cashflow.api.profiles import ProfileStore


class MemoryProfileStore(ProfileStore):
    def __init__(self):
        # An anchor keeps this private shared-memory database alive between requests.
        self.uri = f"file:duemap-{uuid4().hex}?mode=memory&cache=shared"
        self.anchor = sqlite3.connect(self.uri, uri=True, check_same_thread=False)
        self.anchor.execute("PRAGMA max_page_count = 1024")  # At most ~4 MiB/session.
        self.anchor.execute("CREATE TABLE profiles (id TEXT PRIMARY KEY, name_key TEXT UNIQUE NOT NULL, document TEXT NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.uri, uri=True)

    def close(self):
        self.anchor.close()


@dataclass
class Session:
    store: MemoryProfileStore
    touched: float
    active: int = 0
    lock: Lock = field(default_factory=Lock)


class DemoSessions:
    def __init__(self, ttl_seconds=1800, max_sessions=32, clock=monotonic):
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.clock = clock
        self.sessions: dict[str, Session] = {}
        self.lock = Lock()

    def _expire(self):
        for token, session in list(self.sessions.items()):
            if not session.active and self.clock() - session.touched >= self.ttl_seconds:
                session.store.close()
                del self.sessions[token]

    def expire(self):
        with self.lock:
            self._expire()

    def create(self):
        with self.lock:
            self._expire()
            if len(self.sessions) >= self.max_sessions:
                raise HTTPException(503, "The demo is busy. Please try again later.")
            token = secrets.token_urlsafe(32)
            self.sessions[token] = Session(MemoryProfileStore(), self.clock())
            return token

    @contextmanager
    def use(self, token):
        if not token:
            raise HTTPException(401, "Start a demo session before opening a profile.")
        with self.lock:
            self._expire()
            session = self.sessions.get(token)
            if session is None:
                raise HTTPException(410, "Your temporary session ended. Start again and import your downloaded profile.")
            session.active += 1
        try:
            # Serialize a session's mutations while allowing other visitors to work.
            with session.lock:
                yield session.store
        finally:
            with self.lock:
                session.active -= 1
                session.touched = self.clock()

    def close(self):
        with self.lock:
            for session in self.sessions.values():
                session.store.close()
            self.sessions.clear()
