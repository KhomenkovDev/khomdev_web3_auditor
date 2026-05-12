from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from web3_auditor.scanner import get_source_files


class TestGetSourceFiles:
    def _resolve(self, path: Path) -> str:
        return str(path.resolve())

    def test_single_file(self, sample_py_file):
        files = get_source_files(self._resolve(sample_py_file))
        assert len(files) == 1
        assert files[0][0] == self._resolve(sample_py_file)
        assert "def hello()" in files[0][1]

    def test_directory_with_multiple_files(
        self, temp_dir, sample_py_file, sample_sol_file, sample_js_file
    ):
        files = get_source_files(self._resolve(temp_dir))
        assert len(files) == 3
        paths = {f[0] for f in files}
        assert self._resolve(sample_py_file) in paths
        assert self._resolve(sample_sol_file) in paths
        assert self._resolve(sample_js_file) in paths

    def test_ignores_unsupported_extensions(self, temp_dir):
        (temp_dir / "readme.md").write_text("# Readme")
        (temp_dir / "data.json").write_text("{}")
        files = get_source_files(str(temp_dir))
        assert len(files) == 0

    def test_raises_for_nonexistent_path(self):
        with pytest.raises(ValueError, match="does not exist"):
            get_source_files("/nonexistent/path")

    def test_ignores_common_directories(self, temp_dir, sample_py_file):
        (temp_dir / ".git").mkdir()
        (temp_dir / "node_modules").mkdir()
        (temp_dir / "__pycache__").mkdir()
        files = get_source_files(str(temp_dir))
        assert len(files) == 1

    def test_unsupported_single_file(self, temp_dir):
        path = temp_dir / "readme.md"
        path.write_text("# Readme")
        files = get_source_files(str(path))
        assert len(files) == 0

    def test_file_read_error_logged(self, temp_dir):
        path = temp_dir / "broken.py"
        path.write_text("x = 1")
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            files = get_source_files(str(path))
        assert len(files) == 0

    def test_hidden_directories_filtered(self, temp_dir):
        (temp_dir / ".hidden").mkdir()
        (temp_dir / ".hidden" / "nested.py").write_text("x = 1")
        files = get_source_files(str(temp_dir))
        assert len(files) == 0
