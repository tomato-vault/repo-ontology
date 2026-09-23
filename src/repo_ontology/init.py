"""Project initializer for repo-ontology."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional


def get_template_dir() -> Path:
    """Locate the template directory bundled with package or in source tree."""
    # 1. Check beside package (editable / source install)
    candidate1 = Path(__file__).resolve().parent.parent.parent / "template" / ".ontology"
    if candidate1.is_dir():
        return candidate1

    # 2. Check inside package (wheel install)
    candidate2 = Path(__file__).resolve().parent / "template" / ".ontology"
    if candidate2.is_dir():
        return candidate2

    raise FileNotFoundError("Could not locate template/.ontology directory.")


def init_project(target_dir: Optional[Path] = None, force: bool = False) -> Path:
    """Initialize .ontology directory in the target project root."""
    target_root = (target_dir or Path.cwd()).resolve()
    target_onto = target_root / ".ontology"

    if target_onto.exists() and not force:
        raise FileExistsError(
            f"'.ontology' already exists at {target_onto}. Use --force to overwrite."
        )

    template_src = get_template_dir()
    shutil.copytree(template_src, target_onto, dirs_exist_ok=force)
    return target_onto
