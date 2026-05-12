from __future__ import annotations

import asyncio
import time
from typing import Any

from web3_auditor.llm_chat import LLMChatManager

TTL_SECONDS = 3600


class SessionData:
    def __init__(self) -> None:
        self.manager = LLMChatManager()
        self.event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.created_at: float = time.monotonic()
        self.last_active: float = time.monotonic()

    @property
    def is_expired(self) -> bool:
        return time.monotonic() - self.last_active > TTL_SECONDS

    def touch(self) -> None:
        self.last_active = time.monotonic()


_sessions: dict[str, SessionData] = {}


def get_session(session_id: str) -> LLMChatManager:
    _cleanup_expired()
    if session_id not in _sessions:
        _sessions[session_id] = SessionData()
    _sessions[session_id].touch()
    return _sessions[session_id].manager


def get_session_data(session_id: str) -> SessionData:
    _cleanup_expired()
    if session_id not in _sessions:
        _sessions[session_id] = SessionData()
    _sessions[session_id].touch()
    return _sessions[session_id]


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def _cleanup_expired() -> None:
    expired = [sid for sid, s in _sessions.items() if s.is_expired]
    for sid in expired:
        _sessions.pop(sid, None)
