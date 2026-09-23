"""Trace command logic: query ontology and map back to source code."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repo_ontology.loader import OntologyRegistry
from repo_ontology.models import ActionType, FunctionType, ObjectType, RuleSpec


@dataclass
class TraceResult:
    query: str
    domains: List[str] = field(default_factory=list)
    objects: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[Dict[str, Any]] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"# Ontology Trace: `{self.query}`", ""]
        if self.domains:
            lines.append(f"**Matched Domains**: {', '.join(self.domains)}\n")

        lines.append("## 📦 Affected Objects")
        if self.objects:
            for obj in self.objects:
                lines.append(f"- **{obj['name']}** ({obj.get('domain', 'global')}): {obj['description']}")
                props = list(obj.get("properties", {}).keys())
                if props:
                    lines.append(f"  - Properties: {', '.join(props[:8])}{'...' if len(props) > 8 else ''}")
        else:
            lines.append("- *(None)*")
        lines.append("")

        lines.append("## ⚡ Affected Actions")
        if self.actions:
            for act in self.actions:
                target_str = f" → {act['target']['object']}" if act.get("target") else ""
                lines.append(f"- **{act['name']}**{target_str}: {act['description']}")
                if act.get("preconditions"):
                    for p in act["preconditions"]:
                        rule_txt = p.get("rule") or p.get("rule_id") or "Precondition"
                        lines.append(f"  - Precondition: `{rule_txt}`")
        else:
            lines.append("- *(None)*")
        lines.append("")

        lines.append("## 🛡️ Relevant Rules & Invariants")
        if self.rules:
            for r in self.rules:
                scope_str = f" [Scope: {', '.join(r.get('scope', []))}]" if r.get("scope") else ""
                lines.append(f"- **`{r['id']}`** ({r['name']}){scope_str}: {r['description']}")
                if r.get("enforcement"):
                    enf = r["enforcement"]
                    if isinstance(enf, dict):
                        for k, v in enf.items():
                            v_str = ", ".join(v) if isinstance(v, list) else str(v)
                            lines.append(f"  - Enforcement ({k}): {v_str}")
                    elif isinstance(enf, list):
                        lines.append(f"  - Enforcement: {', '.join(enf)}")
                    else:
                        lines.append(f"  - Enforcement: {enf}")
        else:
            lines.append("- *(None)*")
        lines.append("")

        lines.append("## 📂 Source Code Paths")
        if self.affected_files:
            for f in self.affected_files:
                lines.append(f"- `{f}`")
        else:
            lines.append("- *(No direct code paths mapped)*")
        lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def _extract_files(val_data: Any, files_set: Set[str]) -> None:
    if isinstance(val_data, dict):
        for val in val_data.values():
            _extract_files(val, files_set)
    elif isinstance(val_data, list):
        for item in val_data:
            _extract_files(item, files_set)
    elif isinstance(val_data, str) and not val_data.startswith(("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")):
        clean_path = val_data.split(":")[0].strip()
        if clean_path and ("/" in clean_path or clean_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".dart"))):
            files_set.add(clean_path)


def trace_ontology(registry: OntologyRegistry, query: str) -> TraceResult:
    """Find all ontology elements and code paths relevant to query."""
    q = query.lower().strip()
    result = TraceResult(query=query)

    matched_obj_names: Set[str] = set()
    matched_action_names: Set[str] = set()
    matched_func_names: Set[str] = set()
    matched_domains: Set[str] = set()
    matched_rules: List[RuleSpec] = []
    affected_files: Set[str] = set()
    exact_rule_match = any(q == rule.id.lower() for rule in registry.rules)

    # 0. Match Config domains
    if registry.config:
        for d in registry.config.domains:
            if q in d.id.lower() or q in d.name.lower() or (d.description and q in d.description.lower()):
                matched_domains.add(d.id)

    # 1. Match Rules (Direct rule search & enforcement extraction)
    for r in registry.rules:
        is_rule_match = q == r.id.lower() if exact_rule_match else (
            q in r.id.lower()
            or q in r.name.lower()
            or q in r.description.lower()
            or (r.domain and (q in r.domain.lower() or r.domain in matched_domains))
        )
        if is_rule_match:
            matched_rules.append(r)
            if r.domain:
                matched_domains.add(r.domain)
            for sc in r.scope:
                if sc in registry.objects:
                    matched_obj_names.add(sc)
            if r.enforcement:
                _extract_files(r.enforcement, affected_files)

    # 2. Search Objects
    for name, obj in registry.objects.items():
        is_match = not exact_rule_match and (
            q in name.lower()
            or q in obj.description.lower()
            or (obj.domain and (q in obj.domain.lower() or obj.domain in matched_domains))
            or any(q in t.lower() for t in obj.tags)
            or any(q in p.lower() for p in obj.properties.keys())
        )
        if is_match:
            matched_obj_names.add(name)
            if obj.domain:
                matched_domains.add(obj.domain)

    # 3. Search Actions
    for name, act in registry.actions.items():
        is_match = not exact_rule_match and (
            q in name.lower()
            or q in act.description.lower()
            or (act.domain and (q in act.domain.lower() or act.domain in matched_domains))
            or any(q in t.lower() for t in act.tags)
            or (act.target and (act.target.object in matched_obj_names or q in act.target.object.lower()))
            or (act.actor and (act.actor.type in matched_obj_names or q in act.actor.type.lower()))
            or (act.governance and act.governance.feature_id and q in act.governance.feature_id.lower())
        )
        if is_match:
            matched_action_names.add(name)
            if act.domain:
                matched_domains.add(act.domain)
            if act.target and act.target.object in registry.objects:
                matched_obj_names.add(act.target.object)

    # 4. Search Functions
    for name, fn in registry.functions.items():
        is_match = not exact_rule_match and (
            q in name.lower()
            or q in fn.description.lower()
            or (fn.domain and (q in fn.domain.lower() or fn.domain in matched_domains))
            or any(q in t.lower() for t in fn.tags)
            or any(q in inp.lower() for inp in fn.inputs.keys())
        )
        if is_match:
            matched_func_names.add(name)
            if fn.domain:
                matched_domains.add(fn.domain)

    # 5. Populate Rules that intersect with matched objects
    for r in registry.rules:
        if not exact_rule_match and r not in matched_rules:
            if any(o in matched_obj_names for o in r.scope):
                matched_rules.append(r)
                if r.enforcement:
                    _extract_files(r.enforcement, affected_files)

    result.domains = sorted(list(matched_domains))

    # Populate Objects
    for name in sorted(matched_obj_names):
        if name in registry.objects:
            obj = registry.objects[name]
            binding_dict = obj.code_binding.model_dump(by_alias=True, exclude_none=True) if obj.code_binding else {}
            _extract_files(binding_dict, affected_files)

            props_dict = {}
            for pk, pv in obj.properties.items():
                if hasattr(pv, "model_dump"):
                    props_dict[pk] = pv.model_dump(exclude_none=True)
                elif isinstance(pv, dict):
                    props_dict[pk] = pv
                else:
                    props_dict[pk] = {"type": str(pv)}

            result.objects.append(
                {
                    "name": obj.object,
                    "domain": obj.domain,
                    "tags": obj.tags,
                    "description": obj.description,
                    "properties": props_dict,
                    "code_binding": binding_dict,
                }
            )

    # Populate Actions
    for name in sorted(matched_action_names):
        act = registry.actions[name]
        binding_dict = act.code_binding.model_dump(by_alias=True, exclude_none=True) if act.code_binding else {}
        _extract_files(binding_dict, affected_files)
        result.actions.append(
            {
                "name": act.action,
                "domain": act.domain,
                "tags": act.tags,
                "description": act.description,
                "actor": act.actor.model_dump(exclude_none=True) if act.actor else None,
                "target": act.target.model_dump(exclude_none=True) if act.target else None,
                "preconditions": [
                    p.model_dump(exclude_none=True) if hasattr(p, "model_dump") else p
                    for p in act.preconditions
                ],
                "effects": act.effects.model_dump(exclude_none=True) if act.effects else act.effect,
                "code_binding": binding_dict,
                "governance": act.governance.model_dump(exclude_none=True) if act.governance else None,
            }
        )

    # Populate Functions
    for name in sorted(matched_func_names):
        fn = registry.functions[name]
        binding_dict = fn.code_binding.model_dump(by_alias=True, exclude_none=True) if fn.code_binding else {}
        _extract_files(binding_dict, affected_files)
        result.functions.append(
            {
                "name": fn.function,
                "domain": fn.domain,
                "tags": fn.tags,
                "description": fn.description,
                "computation": fn.computation,
                "code_binding": binding_dict,
            }
        )

    # Populate Rules
    for r in matched_rules:
        result.rules.append(
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "scope": r.scope,
                "enforcement": r.enforcement,
            }
        )

    result.affected_files = sorted(list(affected_files))
    return result


def render_trace_result(result: TraceResult) -> None:
    console = Console()
    console.print()
    console.print(Panel(f"[bold cyan]Ontology Trace Query:[/bold cyan] [yellow]{result.query}[/yellow]", expand=False))

    if result.domains:
        console.print(f"[bold green]Matched Domains:[/bold green] {', '.join(result.domains)}")

    # Objects Table
    if result.objects:
        obj_table = Table(title="[bold blue]📦 Affected Objects[/bold blue]")
        obj_table.add_column("Object", style="cyan", no_wrap=True)
        obj_table.add_column("Domain", style="magenta")
        obj_table.add_column("Description", style="white")
        obj_table.add_column("Properties", style="dim")
        for obj in result.objects:
            props = list(obj["properties"].keys())
            props_str = ", ".join(props[:6]) + ("..." if len(props) > 6 else "")
            obj_table.add_row(obj["name"], obj.get("domain") or "-", obj["description"], props_str)
        console.print(obj_table)

    # Actions Table
    if result.actions:
        act_table = Table(title="[bold yellow]⚡ Affected Actions[/bold yellow]")
        act_table.add_column("Action", style="cyan", no_wrap=True)
        act_table.add_column("Target", style="magenta")
        act_table.add_column("Description", style="white")
        for act in result.actions:
            target_str = act["target"]["object"] if act.get("target") else "-"
            act_table.add_row(act["name"], target_str, act["description"])
        console.print(act_table)

    # Rules Table
    if result.rules:
        rule_table = Table(title="[bold red]🛡️ Relevant Invariants & Rules[/bold red]")
        rule_table.add_column("Rule ID", style="bold red", no_wrap=True)
        rule_table.add_column("Name", style="white")
        rule_table.add_column("Scope", style="dim")
        rule_table.add_column("Description", style="italic")
        for r in result.rules:
            scope_str = ", ".join(r.get("scope", []))
            rule_table.add_row(r["id"], r["name"], scope_str, r["description"])
        console.print(rule_table)

    # Affected Files
    if result.affected_files:
        files_table = Table(title="[bold green]📂 Impacted Source Code Paths[/bold green]")
        files_table.add_column("Path", style="green")
        for f in result.affected_files:
            files_table.add_row(f)
        console.print(files_table)
    else:
        console.print("[dim]No direct source code paths mapped to this query.[/dim]")

    console.print()
