"""Entrypoint simples para o Streamlit Community Cloud."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_MAIN = ROOT / "app" / "main.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(APP_MAIN), run_name="__main__")
