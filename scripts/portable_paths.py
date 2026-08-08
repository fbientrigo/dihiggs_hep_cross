"""Portable path discovery for the physical-point MadGraph runner.

Resolves the multi-repo workspace root (DIHIGGS_ROOT) and MadGraph install
location (MG5_HOME) without hard-coding any machine-specific home directory.

Resolution order for the workspace root:
1. ``DIHIGGS_ROOT`` environment variable, if set.
2. Walk upward from this file looking for a directory containing at least two
   of the sibling repositories (``main_dihiggs``, ``ufos``, ``hep_cross``,
   ``llp_recast``, ``boundary``) that make up the workspace. This works both
   from a plain checkout (``<root>/hep_cross``) and from a git worktree
   (``<root>/_worktrees/<name>``).
3. Fall back to the parent of this repository's own root.
"""

from __future__ import annotations

import os
from pathlib import Path

_WORKSPACE_MARKERS = {"main_dihiggs", "ufos", "hep_cross", "llp_recast", "boundary"}


def find_workspace_root(start: Path) -> Path:
    """Return the atlas_dihiggs workspace root containing the sibling repos."""
    env_root = os.environ.get("DIHIGGS_ROOT")
    if env_root:
        return Path(env_root).resolve()

    cur = start.resolve()
    for _ in range(6):
        try:
            siblings = {p.name for p in cur.iterdir() if p.is_dir()}
        except OSError:
            siblings = set()
        if len(siblings & _WORKSPACE_MARKERS) >= 2:
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    return start.parent


def find_mg5_home(default_search: Path | None = None) -> Path | None:
    """Return the MadGraph5_aMC@NLO install directory, or None if not found."""
    env_home = os.environ.get("MG5_HOME")
    if env_home:
        return Path(env_home).resolve()

    search_roots = [Path.home() / ".local" / "mg5amcnlo"]
    if default_search is not None:
        search_roots.append(default_search)

    candidates: list[Path] = []
    for root in search_roots:
        if root.is_dir():
            candidates.extend(p for p in root.iterdir() if p.is_dir())

    if not candidates:
        return None
    return sorted(candidates, key=lambda p: p.name)[-1]
