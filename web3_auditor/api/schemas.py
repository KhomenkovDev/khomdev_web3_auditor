from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class AuditRequest(BaseModel):
    repo_url: Optional[str] = None


class AuditResponse(BaseModel):
    session_id: str
    status: str
    message: str


class SessionStatus(BaseModel):
    id: str
    status: str
    message: str
    risk_score: float
    created_at: str
    updated_at: str
    html_report: Optional[str] = None
