"""Run backend and frontend test suites from one repository command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TestTarget:
    """A test suite command and the directory where it should run."""

    name: str
    command: tuple[str, ...]
    cwd: Path


TEST_TARGETS = {
    "backend": TestTarget(
        name="backend",
        command=(sys.executable, "-m", "pytest", "tests/backend"),
        cwd=REPO_ROOT,
    ),
    "frontend": TestTarget(
        name="frontend",
        command=("npm", "test"),
        cwd=REPO_ROOT / "frontend",
    ),
}


Runner = Callable[..., subprocess.CompletedProcess]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the News Scraper backend and frontend test suites."
    )
    parser.add_argument(
        "target",
        choices=("all", "backend", "frontend"),
        default="all",
        nargs="?",
        help="Test target to run. Defaults to all suites.",
    )
    return parser.parse_args(argv)


def select_targets(target: str) -> tuple[TestTarget, ...]:
    if target == "all":
        return (TEST_TARGETS["backend"], TEST_TARGETS["frontend"])
    return (TEST_TARGETS[target],)


def run_targets(targets: Iterable[TestTarget], runner: Runner = subprocess.run) -> int:
    for target in targets:
        print(f"Running {target.name} tests: {' '.join(target.command)}", flush=True)
        result = runner(target.command, cwd=target.cwd)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: Sequence[str] | None = None, runner: Runner = subprocess.run) -> int:
    args = parse_args(argv)
    return run_targets(select_targets(args.target), runner=runner)


if __name__ == "__main__":
    raise SystemExit(main())
