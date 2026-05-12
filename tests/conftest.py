from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_py_file(temp_dir: Path) -> Path:
    path = temp_dir / "example.py"
    path.write_text("def hello():\n    return 'world'\n")
    return path


@pytest.fixture
def sample_sol_file(temp_dir: Path) -> Path:
    path = temp_dir / "contract.sol"
    path.write_text("pragma solidity ^0.8.0;\ncontract Test {}\n")
    return path


@pytest.fixture
def sample_js_file(temp_dir: Path) -> Path:
    path = temp_dir / "app.js"
    path.write_text("const x = 1;\n")
    return path
