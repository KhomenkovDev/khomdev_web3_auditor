from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Field, SQLModel, JSON, Column


class AuditSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    repo_url: Optional[str] = None
    status: str = "pending"  # pending, cloning, scanning, analyzing, llm, complete, error
    message: str = "Awaiting input..."
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Store findings as JSON
    raw_results: Optional[str] = None
    html_report: Optional[str] = None
    
    # Metadata for the audit
    file_count: int = 0
    risk_score: float = 0.0
    
    def update_status(self, status: str, message: str) -> None:
        self.status = status
        self.message = message
        self.updated_at = datetime.utcnow()
