from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from web3_auditor.github import GitManager


class TestGitManager:
    def test_clone_fails_for_private_repo(self):
        manager = GitManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128,
                ["git", "clone"],
                stderr=b"terminal prompts disabled",
            )
            with pytest.raises(RuntimeError, match="private or require authentication"):
                manager.clone_repository("https://github.com/private/repo.git")

    def test_clone_fails_for_not_found(self):
        manager = GitManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128,
                ["git", "clone"],
                stderr=b"Repository not found",
            )
            with pytest.raises(RuntimeError, match="not found"):
                manager.clone_repository("https://github.com/nonexistent/repo.git")

    def test_clone_fails_with_generic_error(self):
        manager = GitManager()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1,
                ["git", "clone"],
                stderr=b"some other error",
            )
            with pytest.raises(RuntimeError, match="some other error"):
                manager.clone_repository("https://github.com/user/repo.git")

    def test_clone_success(self):
        manager = GitManager()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = manager.clone_repository("https://github.com/public/repo.git")
        assert result is not None
        assert Path(result).is_dir()
        assert manager.temp_dir == result
        manager.cleanup()

    def test_cleanup_removes_temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        manager = GitManager()
        manager.temp_dir = str(tmp)
        (tmp / "some_file").write_text("content")
        manager.cleanup()
        assert not tmp.exists()
        assert manager.temp_dir is None

    def test_cleanup_noop_when_no_temp_dir(self):
        manager = GitManager()
        manager.cleanup()
        assert manager.temp_dir is None

    def test_cleanup_noop_when_dir_missing(self):
        manager = GitManager()
        manager.temp_dir = "/tmp/nonexistent_web3_auditor_test"
        manager.cleanup()
        assert manager.temp_dir == "/tmp/nonexistent_web3_auditor_test"
