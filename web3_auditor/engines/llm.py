from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from google import genai
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GEMINI_")
    api_key: str = ""
    model: str = "gemini-2.5-flash"
    max_retries: int = 5
    initial_delay: int = 4


from web3_auditor.engines.base import Finding


@dataclass
class AuditResult:
    overview: str
    risk_score: float = 0.0
    findings: list[Finding] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    raw_json: str = ""


SYSTEM_PROMPT = """You are an Institutional Web3 Security Auditor. 
Analyze the provided codebase for vulnerabilities, architectural flaws, and performance bottlenecks.
Focus on:
1. Logic errors and edge cases.
2. Smart contract specific vulnerabilities (Reentrancy, Integer Overflow, Access Control).
3. Python/JS security best practices.

Your response MUST be a single valid JSON object with:
- "overview": High-level summary of the codebase.
- "risk_score": A float from 0.0 (Secure) to 10.0 (Critical).
- "findings": An array of objects:
    - "title": Concise name of the issue.
    - "severity": "critical" | "high" | "medium" | "low" | "info".
    - "category": e.g., "Access Control", "Input Validation".
    - "description": Detailed explanation.
    - "file_path": Full path of the file.
    - "line_number": Starting line number (int).
    - "code_snippet": Relevant block of code.
    - "recommendation": Specific fix steps.
- "improvements": Array of strings for general code quality suggestions.

Respond ONLY with JSON."""


class AuditEngine:
    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings()
        self.client = genai.Client(api_key=self.settings.api_key)

    def analyze_codebase(self, files: list[tuple[str, str]]) -> AuditResult:
        context = self._build_context(files)
        prompt = f"### CODEBASE START ###\n{context}\n### CODEBASE END ###\n\n{SYSTEM_PROMPT}"
        
        raw_text = self._send_with_retry(prompt)
        parsed = self._parse_json(raw_text)
        
        if not parsed:
            return AuditResult(overview="Failed to parse AI response.", raw_json=raw_text)
            
        findings = [
            Finding(
                title=f.get("title", "Untitled"),
                severity=f.get("severity", "info"),
                category=f.get("category", "General"),
                description=f.get("description", ""),
                file_path=f.get("file_path"),
                line_number=f.get("line_number"),
                code_snippet=f.get("code_snippet"),
                recommendation=f.get("recommendation")
            )
            for f in parsed.get("findings", [])
        ]
        
        return AuditResult(
            overview=parsed.get("overview", ""),
            risk_score=float(parsed.get("risk_score", 0.0)),
            findings=findings,
            improvements=parsed.get("improvements", []),
            raw_json=raw_text
        )

    def _build_context(self, files: list[tuple[str, str]]) -> str:
        parts = []
        for path, content in files:
            ext = path.split(".")[-1] if "." in path else ""
            parts.append(f"FILE: {path}\n```{ext}\n{content}\n```")
        return "\n\n".join(parts)

    def _send_with_retry(self, prompt: str) -> str:
        delay = self.settings.initial_delay
        for i in range(self.settings.max_retries):
            try:
                chat = self.client.chats.create(model=self.settings.model)
                response = chat.send_message(prompt)
                return cast(str, response.text)
            except Exception as e:
                if i == self.settings.max_retries - 1:
                    raise
                logger.warning("LLM Error (Attempt %d): %s. Retrying...", i+1, e)
                time.sleep(delay)
                delay *= 2
        return ""

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return cast(dict[str, Any], json.loads(text))
        except json.JSONDecodeError:
            return None
