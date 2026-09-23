"""Lint and integrity checking for repo-ontology."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional
from repo_ontology.loader import OntologyRegistry, load_ontology
from repo_ontology.models import CodeBinding


class LintIssue:
    def __init__(self, severity: str, location: str, message: str):
        self.severity = severity  # "ERROR" | "WARNING"
        self.location = location
        self.message = message

    def __str__(self) -> str:
        return f"[{self.severity}] {self.location}: {self.message}"


def _verify_code_path(
    root: Path,
    path_with_symbol: str,
    context: str,
    issues: List[LintIssue],
    strict: bool = False,
) -> None:
    if not path_with_symbol:
        return

    # HTTP API method pattern (e.g., "POST /api/v1/courses/...")
    if path_with_symbol.startswith(("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")):
        return

    parts = path_with_symbol.split(":")
    file_rel_path = parts[0].strip()
    symbol = parts[1].strip() if len(parts) > 1 else None

    target_file = root / file_rel_path
    if not target_file.exists():
        sev = "ERROR" if strict else "WARNING"
        issues.append(
            LintIssue(
                severity=sev,
                location=context,
                message=f"Bound code file does not exist: '{file_rel_path}'",
            )
        )
        return

    # If symbol is specified and file exists, check if symbol exists in file
    if symbol and target_file.is_file():
        try:
            content = target_file.read_text(encoding="utf-8", errors="ignore")
            # Check symbol or class/method parts
            symbols_to_check = [symbol]
            if "." in symbol:
                cls_part, method_part = symbol.split(".", 1)
                symbols_to_check.extend([cls_part, method_part])

            found = any(s in content for s in symbols_to_check)
            if not found:
                issues.append(
                    LintIssue(
                        severity="WARNING",
                        location=context,
                        message=f"Symbol '{symbol}' not found in '{file_rel_path}'",
                    )
                )
        except Exception:
            pass


def _check_binding(
    root: Path,
    binding: Optional[CodeBinding],
    context: str,
    issues: List[LintIssue],
    strict: bool = False,
) -> None:
    if not binding:
        return

    if binding.backend:
        if binding.backend.model:
            _verify_code_path(root, binding.backend.model, f"{context} -> backend.model", issues, strict)
        if binding.backend.schema_:
            _verify_code_path(root, binding.backend.schema_, f"{context} -> backend.schema", issues, strict)
        if binding.backend.service:
            _verify_code_path(root, binding.backend.service, f"{context} -> backend.service", issues, strict)

    if binding.frontend:
        if binding.frontend.entity:
            _verify_code_path(root, binding.frontend.entity, f"{context} -> frontend.entity", issues, strict)
        if binding.frontend.feature:
            _verify_code_path(root, binding.frontend.feature, f"{context} -> frontend.feature", issues, strict)

    if binding.mobile:
        if binding.mobile.model:
            _verify_code_path(root, binding.mobile.model, f"{context} -> mobile.model", issues, strict)
        if binding.mobile.viewmodel:
            _verify_code_path(root, binding.mobile.viewmodel, f"{context} -> mobile.viewmodel", issues, strict)


def lint_ontology(
    registry: OntologyRegistry,
    check_code: bool = True,
    strict_code: bool = False,
) -> List[LintIssue]:
    """Run lint checks across the parsed ontology."""
    issues: List[LintIssue] = []

    # 1. Parsing errors from loader
    for err in registry.errors:
        issues.append(
            LintIssue(
                severity="ERROR",
                location=str(err.file_path.relative_to(registry.root_path)),
                message=err.message,
            )
        )

    # 2. Referential integrity: Link sources and targets
    for link in registry.links:
        if link.source not in registry.objects:
            issues.append(
                LintIssue(
                    severity="ERROR",
                    location=f"Link '{link.name}'",
                    message=f"Source object '{link.source}' is not defined in objects/",
                )
            )
        if link.target not in registry.objects:
            issues.append(
                LintIssue(
                    severity="ERROR",
                    location=f"Link '{link.name}'",
                    message=f"Target object '{link.target}' is not defined in objects/",
                )
            )

    # 3. Action target integrity
    for act_name, act in registry.actions.items():
        if act.target and act.target.object not in registry.objects:
            issues.append(
                LintIssue(
                    severity="ERROR",
                    location=f"Action '{act_name}'",
                    message=f"Target object '{act.target.object}' is not defined in objects/",
                )
            )

        if act.actor and act.actor.type not in registry.objects:
            issues.append(
                LintIssue(
                    severity="WARNING",
                    location=f"Action '{act_name}'",
                    message=f"Actor type '{act.actor.type}' is not registered as an object.",
                )
            )

        # Governance references
        if act.governance and act.governance.adr:
            adr_path = registry.root_path / act.governance.adr
            if not adr_path.exists():
                issues.append(
                    LintIssue(
                        severity="WARNING",
                        location=f"Action '{act_name}' governance",
                        message=f"Referenced ADR does not exist: '{act.governance.adr}'",
                    )
                )

    # 4. Rules scope integrity
    for rule in registry.rules:
        for scope_obj in rule.scope:
            if scope_obj not in registry.objects:
                issues.append(
                    LintIssue(
                        severity="WARNING",
                        location=f"Rule '{rule.id}'",
                        message=f"Scope object '{scope_obj}' is not defined in objects/",
                    )
                )

    # 5. Code binding checks
    if check_code:
        for obj_name, obj in registry.objects.items():
            _check_binding(registry.root_path, obj.code_binding, f"Object '{obj_name}'", issues, strict_code)

        for act_name, act in registry.actions.items():
            _check_binding(registry.root_path, act.code_binding, f"Action '{act_name}'", issues, strict_code)

        for fn_name, fn in registry.functions.items():
            _check_binding(registry.root_path, fn.code_binding, f"Function '{fn_name}'", issues, strict_code)

    return issues
