from __future__ import annotations

import re
from pathlib import Path

_SOL_IMPORT_RE = re.compile(r'import\s+(?:"([^"]+)"|\'([^\']+)\')')
_SOL_IMPORT_FROM_RE = re.compile(r"import\s+\{([^}]+)\}\s+from\s+(?:\"([^\"]+)\"|\'([^\']+)\')")
_PY_IMPORT_RE = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)
_PY_FROM_IMPORT_RE = re.compile(r"^from\s+([\w.]+)\s+import", re.MULTILINE)


def get_dot_imports(file_path: Path) -> set[str]:
    deps: set[str] = set()
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return deps
    suffix = file_path.suffix
    if suffix == ".sol":
        for m in _SOL_IMPORT_RE.finditer(text):
            dep = m.group(1) or m.group(2)
            deps.add(dep)
        for m in _SOL_IMPORT_FROM_RE.finditer(text):
            dep = m.group(2) or m.group(3)
            deps.add(dep)
    elif suffix == ".py":
        for m in _PY_IMPORT_RE.finditer(text):
            deps.add(m.group(1))
        for m in _PY_FROM_IMPORT_RE.finditer(text):
            deps.add(m.group(1))
    return deps


def build_dependency_graph(files: list[tuple[str, str]]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for file_path_str, _content in files:
        path = Path(file_path_str)
        deps = get_dot_imports(path)
        graph[str(path)] = deps
    return graph
