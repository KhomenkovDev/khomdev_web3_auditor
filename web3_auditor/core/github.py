from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?$"
)


class GitManager:
    def __init__(self) -> None:
        self.temp_dir: str | None = None

    def clone_repository(self, repo_url: str) -> Path:
        if not GITHUB_URL_RE.match(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
            
        self.temp_dir = tempfile.mkdtemp(prefix="web3_auditor_clone_")
        try:
            logger.info("Cloning %s into %s", repo_url, self.temp_dir)
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, self.temp_dir],
                check=True,
                capture_output=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            return Path(self.temp_dir)
        except subprocess.CalledProcessError as e:
            self.cleanup()
            stderr = e.stderr.decode("utf-8")
            logger.error("Clone failed: %s", stderr)
            raise RuntimeError(f"Git clone failed: {stderr}") from e

    def cleanup(self) -> None:
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
