from pathlib import Path


MAX_PYTHON_FILE_LINES = 300
EXCLUDED_PARTS = {".git", ".pytest_cache", ".venv", "__pycache__"}
REPO_ROOT = Path(__file__).resolve().parents[1]


def project_python_files():
    for path in REPO_ROOT.rglob("*.py"):
        relative_parts = path.relative_to(REPO_ROOT).parts
        if any(part in EXCLUDED_PARTS for part in relative_parts):
            continue
        yield path


def test_project_python_files_stay_under_300_lines():
    oversized = []
    for path in project_python_files():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_FILE_LINES:
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            oversized.append(f"{relative_path}: {line_count}")

    assert oversized == []
