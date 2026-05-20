from pathlib import Path


MAX_PYTHON_FILE_LINES = 300
EXCLUDED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}


def project_python_files():
    root = Path(__file__).resolve().parents[1]
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        yield path


def test_project_python_files_stay_under_300_lines():
    oversized = []
    for path in project_python_files():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_FILE_LINES:
            oversized.append(f"{path.relative_to(path.parents[1])}: {line_count}")

    assert oversized == []