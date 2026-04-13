"""Validate Jobs2Go OpenAPI JSON examples parse correctly."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "openapi" / "examples"
    files = sorted(root.rglob("*.json"))
    if not files:
        raise SystemExit("No JSON example files found")

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)

    print(f"Validated {len(files)} JSON example files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
