import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: F401

for name in (
    "app_pages/home.py",
    "app_pages/upload.py",
    "app_pages/analyze.py",
    "app_pages/edit_resume.py",
    "app_pages/interview.py",
):
    path = ROOT / name
    assert path.exists(), path

print("import_check ok")
