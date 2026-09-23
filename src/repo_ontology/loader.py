"""Loader for repo-ontology files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import ValidationError

from repo_ontology.models import (
    ActionType,
    FunctionType,
    LinkSpec,
    LinkTypeDoc,
    ObjectType,
    OntologyConfig,
    RuleSpec,
    RuleTypeDoc,
)


class LoadError:
    def __init__(self, file_path: Path, message: str, exception: Optional[Exception] = None):
        self.file_path = file_path
        self.message = message
        self.exception = exception

    def __str__(self) -> str:
        return f"{self.file_path}: {self.message}"


class OntologyRegistry:
    def __init__(self, root_path: Path, ontology_dir: Path):
        self.root_path = root_path
        self.ontology_dir = ontology_dir
        self.config: Optional[OntologyConfig] = None
        self.objects: Dict[str, ObjectType] = {}
        self.links: List[LinkSpec] = []
        self.actions: Dict[str, ActionType] = {}
        self.functions: Dict[str, FunctionType] = {}
        self.rules: List[RuleSpec] = []
        self.errors: List[LoadError] = []

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def find_ontology_dir(start_path: Optional[Path] = None) -> Optional[Path]:
    """Search for .ontology directory starting from start_path upwards."""
    current = (start_path or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        onto_dir = parent / ".ontology"
        if onto_dir.is_dir():
            return onto_dir
    return None


def load_ontology(project_root: Optional[Path] = None) -> OntologyRegistry:
    """Load and parse the full ontology from the project root or closest .ontology dir."""
    if project_root is None:
        onto_dir = find_ontology_dir()
        if onto_dir is None:
            raise FileNotFoundError("Could not find '.ontology' directory in current or parent paths.")
        root = onto_dir.parent
    else:
        root = project_root.resolve()
        onto_dir = root / ".ontology"
        if not onto_dir.is_dir():
            raise FileNotFoundError(f"No '.ontology' directory found at {root}")

    registry = OntologyRegistry(root_path=root, ontology_dir=onto_dir)

    # 1. Load config.yml
    config_file = onto_dir / "config.yml"
    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            registry.config = OntologyConfig.model_validate(data)
        except Exception as e:
            registry.errors.append(LoadError(config_file, f"Failed to parse config: {e}", e))
    else:
        registry.config = OntologyConfig()

    # 2. Load objects/
    obj_dir = onto_dir / "objects"
    if obj_dir.is_dir():
        for path in sorted(obj_dir.glob("*.yml")) + sorted(obj_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                obj = ObjectType.model_validate(data)
                registry.objects[obj.object] = obj
            except Exception as e:
                registry.errors.append(LoadError(path, f"Object parse error: {e}", e))

    # 3. Load links/
    link_dir = onto_dir / "links"
    if link_dir.is_dir():
        for path in sorted(link_dir.glob("*.yml")) + sorted(link_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                link_doc = LinkTypeDoc.model_validate(data)
                registry.links.extend(link_doc.links)
            except Exception as e:
                registry.errors.append(LoadError(path, f"Link parse error: {e}", e))

    # 4. Load actions/
    action_dir = onto_dir / "actions"
    if action_dir.is_dir():
        for path in sorted(action_dir.glob("*.yml")) + sorted(action_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                act = ActionType.model_validate(data)
                registry.actions[act.action] = act
            except Exception as e:
                registry.errors.append(LoadError(path, f"Action parse error: {e}", e))

    # 5. Load functions/
    func_dir = onto_dir / "functions"
    if func_dir.is_dir():
        for path in sorted(func_dir.glob("*.yml")) + sorted(func_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                fn = FunctionType.model_validate(data)
                registry.functions[fn.function] = fn
            except Exception as e:
                registry.errors.append(LoadError(path, f"Function parse error: {e}", e))

    # 6. Load rules/
    rule_dir = onto_dir / "rules"
    if rule_dir.is_dir():
        for path in sorted(rule_dir.glob("*.yml")) + sorted(rule_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                rule_doc = RuleTypeDoc.model_validate(data)
                registry.rules.extend(rule_doc.rules)
            except Exception as e:
                registry.errors.append(LoadError(path, f"Rule parse error: {e}", e))

    return registry
