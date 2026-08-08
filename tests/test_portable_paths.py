"""Unit tests for portable workspace-root and MG5 discovery."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from portable_paths import find_mg5_home, find_workspace_root


def test_workspace_root_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DIHIGGS_ROOT", str(tmp_path))
    assert find_workspace_root(REPO_ROOT) == tmp_path.resolve()


def test_workspace_root_discovers_sibling_repos(monkeypatch, tmp_path):
    monkeypatch.delenv("DIHIGGS_ROOT", raising=False)
    workspace = tmp_path / "atlas_dihiggs"
    (workspace / "main_dihiggs").mkdir(parents=True)
    (workspace / "hep_cross").mkdir()
    nested_worktree = workspace / "_worktrees" / "some-branch"
    nested_worktree.mkdir(parents=True)

    assert find_workspace_root(nested_worktree) == workspace.resolve()


def test_workspace_root_falls_back_to_parent_when_no_markers(monkeypatch, tmp_path):
    monkeypatch.delenv("DIHIGGS_ROOT", raising=False)
    lonely = tmp_path / "somewhere" / "isolated"
    lonely.mkdir(parents=True)
    assert find_workspace_root(lonely) == lonely.parent


def test_mg5_home_honors_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MG5_HOME", str(tmp_path))
    assert find_mg5_home() == tmp_path.resolve()


def test_mg5_home_picks_highest_version_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("MG5_HOME", raising=False)
    fake_home = tmp_path / "home"
    mg5_root = fake_home / ".local" / "mg5amcnlo"
    (mg5_root / "3.5.1").mkdir(parents=True)
    (mg5_root / "3.5.3").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    assert find_mg5_home().name == "3.5.3"


def test_mg5_home_returns_none_when_absent(monkeypatch, tmp_path):
    monkeypatch.delenv("MG5_HOME", raising=False)
    fake_home = tmp_path / "empty_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    assert find_mg5_home() is None
