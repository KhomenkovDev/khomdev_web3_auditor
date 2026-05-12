from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Literal

from web3_auditor.engines.base import AnalyzerResult, Finding

logger = logging.getLogger(__name__)


def run_slither(target_path: str) -> AnalyzerResult:
    result = AnalyzerResult()
    slither_path = shutil.which("slither")
    if slither_path is None:
        logger.warning("slither not found on PATH, skipping")
        return result
    try:
        proc = subprocess.run(
            [slither_path, target_path, "--json", "-"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        result.raw_output = proc.stdout
        if proc.returncode != 0:
            logger.warning("slither exited with code %d: %s", proc.returncode, proc.stderr[:500])
        _parse_slither_output(proc.stdout, result)
    except subprocess.TimeoutExpired:
        logger.warning("slither timed out on %s", target_path)
    except Exception:
        logger.exception("slither runner failed")
    return result


def _parse_slither_output(raw: str, result: AnalyzerResult) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    for detector in data.get("detectors", data.get("results", [])):
        severity_raw: str = detector.get("impact", detector.get("severity", "medium"))
        elements = detector.get("elements", [])
        file_path = None
        line_number = None
        if elements:
            source = elements[0].get("source_mapping", {})
            file_path = source.get("filename_relative") or source.get("filename")
            line_number = source.get("line")
        result.findings.append(
            Finding(
                title=detector.get("check", detector.get("title", "Unknown")),
                severity=_map_slither_severity(severity_raw),
                category=detector.get("impact", "unknown"),
                description=detector.get("description", ""),
                file_path=file_path,
                line_number=line_number,
                recommendation=detector.get("recommendation"),
                tool="slither",
            )
        )


def _map_slither_severity(impact: str) -> Literal["critical", "high", "medium", "low", "info"]:
    mapping: dict[str, Literal["critical", "high", "medium", "low", "info"]] = {
        "high": "high",
        "medium": "medium",
        "low": "low",
        "informational": "info",
        "optimization": "info",
    }
    return mapping.get(impact.lower(), "medium")
