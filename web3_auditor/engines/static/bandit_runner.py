from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Literal

from web3_auditor.engines.base import AnalyzerResult, Finding

logger = logging.getLogger(__name__)


def run_bandit(target_path: str) -> AnalyzerResult:
    result = AnalyzerResult()
    bandit_path = shutil.which("bandit")
    if bandit_path is None:
        logger.warning("bandit not found on PATH, skipping")
        return result
    try:
        proc = subprocess.run(
            [bandit_path, "-r", target_path, "-f", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        result.raw_output = proc.stdout
        if proc.returncode not in (0, 1):
            logger.warning("bandit exited with code %d: %s", proc.returncode, proc.stderr[:500])
        _parse_bandit_output(proc.stdout, result)
    except subprocess.TimeoutExpired:
        logger.warning("bandit timed out on %s", target_path)
    except Exception:
        logger.exception("bandit runner failed")
    return result


def _parse_bandit_output(raw: str, result: AnalyzerResult) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    for issue in data.get("results", []):
        severity_raw: str = issue.get("issue_severity", "MEDIUM")
        sev = _map_bandit_severity(severity_raw)
        result.findings.append(
            Finding(
                title=issue.get("test_name", issue.get("issue_text", "Unknown")),
                severity=sev,
                category=issue.get("issue_text", ""),
                description=issue.get("issue_text", ""),
                file_path=issue.get("filename"),
                line_number=issue.get("line_number"),
                code_snippet=issue.get("code"),
                recommendation=issue.get("recommendation"),
                tool="bandit",
            )
        )


def _map_bandit_severity(severity: str) -> Literal["critical", "high", "medium", "low", "info"]:
    mapping: dict[str, Literal["critical", "high", "medium", "low", "info"]] = {
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
    }
    return mapping.get(severity.upper(), "medium")
