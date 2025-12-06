"""Uruchomienie optymalizacji trasy dostaw."""

from __future__ import annotations

import sys
from pathlib import Path

# Umożliwia uruchomienie bez ustawiania PYTHONPATH/instalacji pakietu.
repo_root = Path(__file__).resolve().parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ga_delivery.cli import main  # noqa: E402


if __name__ == "__main__":
    # Domyślnie włącz interaktywny wybór punktów przy uruchomieniu main.py.
    if "--interactive" not in sys.argv:
        sys.argv.append("--interactive")
    main()
