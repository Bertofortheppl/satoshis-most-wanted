"""Wrapper around the vendored trapcheck scanner (services/trapcheck/).

Vendoring policy: ATTRIBUTION.md — upstream file is never modified; this
wrapper normalizes its JSON into our schema's TrapScan. The scanner is
invoked as a subprocess (stdlib-only, no network in --path mode).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .schema import TrapScan

VENDORED_DIR = Path(__file__).resolve().parents[1] / "trapcheck"
SCANNER = VENDORED_DIR / "trapcheck.py"


def _upstream_commit() -> str:
    up = VENDORED_DIR / "UPSTREAM"
    return up.read_text().strip().split()[0] if up.exists() else ""


def _run(args: list[str], timeout: int = 180) -> dict:
    env = dict(os.environ)
    if env.get("GITHUB_TOKEN") == "":
        env.pop("GITHUB_TOKEN")
    proc = subprocess.run(
        [sys.executable, str(SCANNER), *args, "--json"],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"trapcheck produced no JSON (rc={proc.returncode}): "
            f"{proc.stdout[:300]} {proc.stderr[:300]}"
        )


def _normalize(res: dict) -> TrapScan:
    return TrapScan(
        verdict=res["verdict"],
        score=res["score"],
        rules=[
            {
                "rule": f["rule"],
                "severity": f["severity"],
                "title": f.get("title", ""),
                "why": f.get("why", ""),
                "evidence": f.get("evidence", ""),
                "source": f.get("source", ""),
            }
            for f in res.get("findings", [])
        ],
        target=res.get("target", ""),
        upstream_commit=_upstream_commit(),
        checked_at=res.get("checked") or "",
    )


def scan_path(path) -> TrapScan:
    """Hermetic: scan a checked-out working tree. No network."""
    return _normalize(_run(["--path", str(path)]))


def scan_github(target: str, token: Optional[str] = None) -> TrapScan:
    """Network: scan owner/repo or owner/repo#issue via the GitHub API."""
    prev = os.environ.get("GITHUB_TOKEN")
    if token:
        os.environ["GITHUB_TOKEN"] = token
    try:
        return _normalize(_run([target]))
    finally:
        if token:
            if prev is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = prev


def exit_code(trap: TrapScan) -> int:
    """Upstream CI-gating semantics: 0 clean/caution, 1 suspicious, 2 trap."""
    return {"TRAP": 2, "SUSPICIOUS": 1}.get(trap.verdict, 0)
