#!/usr/bin/env python3
"""Render the Ludus Nomad range config with small local customizations."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "range-config.nomad-cluster.yml"
DIST_DIR = ROOT / ".dist"
OUTPUT = DIST_DIR / "range-config.nomad-cluster.rendered.yml"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    config = SOURCE.read_text(encoding="utf-8")
    demo_enabled = "true" if env_bool("NOMAD_DEPLOY_HELLO_WORLD", False) else "false"
    config = config.replace("nomad_deploy_demo_job: false", f"nomad_deploy_demo_job: {demo_enabled}", 1)
    OUTPUT.write_text(config, encoding="utf-8")
    print(f"Rendered {OUTPUT}")
    print(f"NOMAD_DEPLOY_HELLO_WORLD={demo_enabled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
