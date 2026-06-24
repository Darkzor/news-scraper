import subprocess
import sys

from scripts.run_tests import REPO_ROOT, main, run_targets, select_targets


def test_select_targets_defaults_to_backend_then_frontend() -> None:
    targets = select_targets("all")

    assert [target.name for target in targets] == ["backend", "frontend"]
    assert targets[0].command == (sys.executable, "-m", "pytest", "tests/backend")
    assert targets[1].command == ("npm", "test")


def test_select_targets_can_limit_to_frontend() -> None:
    targets = select_targets("frontend")

    assert len(targets) == 1
    assert targets[0].name == "frontend"
    assert targets[0].cwd == REPO_ROOT / "frontend"


def test_run_targets_stops_on_first_failure() -> None:
    calls = []

    def runner(command, cwd):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 7)

    exit_code = run_targets(select_targets("all"), runner=runner)

    assert exit_code == 7
    assert len(calls) == 1
    assert calls[0][1] == REPO_ROOT


def test_main_runs_requested_backend_target() -> None:
    calls = []

    def runner(command, cwd):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    exit_code = main(["backend"], runner=runner)

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][1] == REPO_ROOT
