import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))
else:
    raise RuntimeError(f"src directory not found at {SRC_DIR}")
