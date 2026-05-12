from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from web3_auditor.api.schemas import AuditRequest, AuditResponse, SessionStatus
from web3_auditor.core.github import GitManager
from web3_auditor.core.scanner import CodeScanner
from web3_auditor.db.database import get_session
from web3_auditor.db.models import AuditSession
from web3_auditor.engines.llm import AuditEngine

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


async def run_audit_task(session_id: str):
    # This runs in the background
    from web3_auditor.db.database import engine
    
    with Session(engine) as db:
        session = db.get(AuditSession, session_id)
        if not session:
            return

        try:
            # 1. Cloning
            session.update_status("cloning", "Cloning repository...")
            db.add(session)
            db.commit()
            
            git = GitManager()
            repo_path = git.clone_repository(session.repo_url)
            
            # 2. Scanning
            session.update_status("scanning", "Scanning source files...")
            db.add(session)
            db.commit()
            
            files = CodeScanner.get_source_files(repo_path)
            session.file_count = len(files)
            
            if not files:
                raise ValueError("No supported files found.")

            # 3. Analyzing (Static + LLM)
            session.update_status("analyzing", "Synthesizing security results...")
            db.add(session)
            db.commit()
            
            engine_ai = AuditEngine()
            result = engine_ai.analyze_codebase(files)
            
            # 4. Finalizing
            session.risk_score = result.risk_score
            session.raw_results = result.raw_json
            
            # Basic markdown to HTML for report (we can improve this later with a dedicated template)
            import markdown
            session.html_report = markdown.markdown(result.overview, extensions=["fenced_code", "codehilite"])
            
            session.update_status("complete", "Audit finished successfully.")
            db.add(session)
            db.commit()
            
        except Exception as e:
            logger.exception("Audit task failed for session %s", session_id)
            session.update_status("error", f"Error: {str(e)}")
            db.add(session)
            db.commit()
        finally:
            if 'git' in locals():
                git.cleanup()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/audit", response_model=AuditResponse)
async def start_audit(
    request: AuditRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_session)
):
    if not request.repo_url:
        raise HTTPException(status_code=400, detail="Repo URL is required.")
        
    session = AuditSession(repo_url=request.repo_url)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    background_tasks.add_task(run_audit_task, session.id)
    
    return AuditResponse(
        session_id=session.id,
        status=session.status,
        message=session.message
    )


@router.get("/api/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str, db: Session = Depends(get_session)):
    session = db.get(AuditSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    return SessionStatus(
        id=session.id,
        status=session.status,
        message=session.message,
        risk_score=session.risk_score,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        html_report=session.html_report
    )
