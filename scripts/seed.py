"""Wrapper that runs the seed_catalog Django management command.

Usage (from the repo root):

    cd apps/api
    poetry run python ../../scripts/seed.py

The command itself is implemented in
``apps/api/apps/catalog/management/commands/seed_catalog.py``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    api_dir = Path(__file__).resolve().parent.parent / "apps" / "api"
    if not api_dir.exists():
        raise SystemExit(f"Could not find {api_dir}; run from the repo root.")
    os.chdir(api_dir)
    sys.path.insert(0, str(api_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()
    from django.core.management import call_command

    call_command("seed_catalog")


if __name__ == "__main__":
    main()
