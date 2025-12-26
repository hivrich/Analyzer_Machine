import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT

while PARENT and PARENT.name:
    if (PARENT / "app").exists():
        sys.path.insert(0, str(PARENT))
        break
    PARENT = PARENT.parent
