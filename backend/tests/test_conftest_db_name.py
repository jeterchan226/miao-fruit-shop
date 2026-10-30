from pathlib import Path

import pytest

from tests.conftest import resolve_test_db_name


@pytest.fixture(autouse=True)
def no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DB_NAME", raising=False)


def test_main_checkout_uses_miao_test(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert resolve_test_db_name(tmp_path) == "miao_test"


def test_linked_worktree_gets_own_db(tmp_path: Path) -> None:
    root = tmp_path / "Amazing-Bohr-9c527f"
    root.mkdir()
    (root / ".git").write_text("gitdir: /repo/.git/worktrees/x\n")
    assert resolve_test_db_name(root) == "miao_test_amazing_bohr_9c527f"


def test_long_worktree_name_fits_postgres_identifier_limit(tmp_path: Path) -> None:
    root = tmp_path / ("w" * 100)
    root.mkdir()
    (root / ".git").write_text("gitdir: /repo/.git/worktrees/x\n")
    assert len(resolve_test_db_name(root)) <= 63


def test_env_override_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".git").write_text("gitdir: /repo/.git/worktrees/x\n")
    monkeypatch.setenv("TEST_DB_NAME", "miao_custom")
    assert resolve_test_db_name(tmp_path) == "miao_custom"
