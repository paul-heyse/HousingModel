#!/usr/bin/env python3
"""Lightweight documentation compliance checks.

The script runs on CI to make sure spec-driven documentation stays aligned with
implementation. It verifies that knowledge base entries exist for every OpenSpec
capability, that critical modules expose intent-rich docstrings, and that
runbooks accompany capability briefs.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = REPO_ROOT / "docs" / "knowledge_base"
SPECS_DIR = REPO_ROOT / "openspec" / "specs"

# Mapping from spec capability directory to knowledge base slug
CAPABILITY_TO_SLUG = {
    "core": "core-runtime",
    "etl": "etl-pipelines",
    "exports": "exports-suite",
    "geo": "geo-services",
    "governance": "governance-workflows",
    "gui": "gui-analytics",
    "jobs": "jobs-orchestration",
}

TARGET_DOCSTRING_MODULES = {
    "src/aker_core/__init__.py": {
        "module": True,
        "functions": [],
    },
    "src/aker_core/run.py": {
        "module": True,
        "functions": ["_hash_snapshot", "_derive_seed", "_apply_seed"],
    },
    "src/aker_core/markets/service.py": {
        "module": False,
        "functions": ["_favor_higher", "_favor_lower"],
    },
    "src/aker_core/exports/__init__.py": {
        "module": True,
        "functions": [],
    },
    "src/aker_geo/terrain/__init__.py": {
        "module": True,
        "functions": [],
    },
}


def fail(message: str) -> None:
    """Print a failure message and exit with non-zero status."""

    print(f"[documentation] {message}", file=sys.stderr)
    sys.exit(1)


def check_capability_pages() -> None:
    """Ensure each spec capability has a knowledge base brief and runbook."""

    missing_briefs: list[str] = []
    missing_runbooks: list[str] = []
    missing_change_log: list[str] = []

    for capability_dir in sorted(d for d in SPECS_DIR.iterdir() if d.is_dir()):
        capability = capability_dir.name
        slug = CAPABILITY_TO_SLUG.get(capability)
        if slug is None:
            fail(
                f"No knowledge base slug configured for capability '{capability}'."
            )

        brief_path = KNOWLEDGE_BASE / "capabilities" / f"{slug}.md"
        runbook_path = KNOWLEDGE_BASE / "runbooks" / f"{slug}.md"
        if not brief_path.exists():
            missing_briefs.append(capability)
        else:
            content = brief_path.read_text(encoding="utf-8")
            if "## Change Log" not in content:
                missing_change_log.append(capability)
        if not runbook_path.exists():
            missing_runbooks.append(capability)

    problems: list[str] = []
    if missing_briefs:
        problems.append(
            "missing capability briefs for: " + ", ".join(sorted(missing_briefs))
        )
    if missing_runbooks:
        problems.append(
            "missing runbooks for: " + ", ".join(sorted(missing_runbooks))
        )
    if missing_change_log:
        problems.append(
            "capability briefs missing Change Log section: "
            + ", ".join(sorted(missing_change_log))
        )

    if problems:
        fail("; ".join(problems))


def check_docstrings() -> None:
    """Ensure specified modules and functions include docstrings."""

    for relative, expectations in TARGET_DOCSTRING_MODULES.items():
        module_path = REPO_ROOT / relative
        if not module_path.exists():
            fail(f"expected module missing: {relative}")
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        if expectations.get("module") and ast.get_docstring(tree) in {None, ""}:
            fail(f"module '{relative}' lacks required docstring")

        functions = {
            node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        for func_name in expectations.get("functions", []):
            node = functions.get(func_name)
            if node is None:
                fail(f"function '{func_name}' not found in '{relative}'")
            if ast.get_docstring(node) in {None, ""}:
                fail(f"function '{relative}:{func_name}' lacks docstring")


def main() -> None:
    check_capability_pages()
    check_docstrings()
    print("[documentation] all knowledge base and docstring checks passed")


if __name__ == "__main__":
    main()
