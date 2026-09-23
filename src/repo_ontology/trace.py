"""Requirement-to-code tracing engine for repo-ontology."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Set
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
        lines: List[str] = []
        lines.append(f"# Ontology Trace: '{self.query}'")
        lines.append("")

        if self.domains:
            lines.append(f"**Matched Domains**: {', '.join(self.domains)}")
            lines.append("")

        # 1. Objects
        lines.append("## 1. Domain Objects (실체 및 데이터 모델)")
        if not self.objects:
            lines.append("- (No directly matching objects)")
        else:
            for obj in self.objects:
                lines.append(f"### `{obj['name']}` ({obj.get('description', '')})")
                if obj.get("tags"):
                    lines.append(f"- **Tags**: `{', '.join(obj['tags'])}`")
                if obj.get("code_binding"):
                    lines.append(f"- **Code Binding**: `{obj['code_binding']}`")
                props = obj.get("properties", {})
                if props:
                    prop_list = [f"`{k}` ({v.get('type')})" for k, v in props.items()]
                    lines.append(f"- **Properties**: {', '.join(prop_list[:6])}" + ("..." if len(prop_list) > 6 else ""))
                lines.append("")

        # 2. Actions
        lines.append("## 2. Actions & Transactions (상태 변경 및 불변식 가드)")
        if not self.actions:
            lines.append("- (No directly matching actions)")
        else:
            for act in self.actions:
                lines.append(f"### `{act['name']}`")
                lines.append(f"- **Description**: {act.get('description', '')}")
                lines.append(f"- **Actor**: `{act.get('actor')}` -> **Target**: `{act.get('target')}`")
                if act.get("preconditions"):
                    lines.append("- **Preconditions (불변식)**:")
                    for pre in act["preconditions"]:
                        lines.append(f"  - `{pre.get('rule')}` -> *\"{pre.get('error')}\"*")
                if act.get("code_binding"):
                    lines.append(f"- **Code Binding**:")
                    for k, v in act["code_binding"].items():
                        lines.append(f"  - {k}: `{v}`")
                if act.get("governance"):
                    gov = act["governance"]
                    lines.append(f"- **Governance**: Feature `{gov.get('feature_id')}`, ADR `{gov.get('adr')}`")
                lines.append("")

        # 3. Functions
        lines.append("## 3. Pure Functions & Computations (계산 및 도출 로직)")
        if not self.functions:
            lines.append("- (No directly matching functions)")
        else:
            for fn in self.functions:
                lines.append(f"### `{fn['name']}`")
                lines.append(f"- **Description**: {fn.get('description', '')}")
                if fn.get("computation"):
                    lines.append(f"- **Computation**: `{fn['computation']}`")
                if fn.get("code_binding"):
                    lines.append(f"- **Code Binding**: `{fn['code_binding']}`")
                lines.append("")

        # 4. Rules
        lines.append("## 4. Invariant Rules (전역 정책)")
        if not self.rules:
            lines.append("- (No matching domain rules)")
        else:
            for r in self.rules:
                lines.append(f"- **[{r['id']}] {r['name']}**: {r['description']} (Scope: `{r.get('scope')}`)")
        lines.append("")

        # 5. Affected Files Unique List
        lines.append("## 5. Direct Code Touchpoints (수정 대상 파일 목록)")
        if not self.affected_files:
            lines.append("- (No bound code files identified)")
        else:
            for f in self.affected_files:
                lines.append(f"- `{f}`")
        lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def _extract_files(binding_dict: Dict[str, Any], files_set: Set[str]) -> None:
    for val in binding_dict.values():
        if isinstance(val, dict):
            _extract_files(val, files_set)
        elif isinstance(val, str) and not val.startswith(("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")):
            clean_path = val.split(":")[0].strip()
            if clean_path:
                files_set.add(clean_path)


def trace_ontology(registry: OntologyRegistry, query: str) -> TraceResult:
    """Find all ontology elements and code paths relevant to query."""
    q = query.lower().strip()
    result = TraceResult(query=query)

    matched_obj_names: Set[str] = set()
    matched_action_names: Set[str] = set()
    matched_func_names: Set[str] = set()
    matched_domains: Set[str] = set()
    affected_files: Set[str] = set()

    # Match Config domains
    if registry.config:
        for d in registry.config.domains:
            if q in d.id.lower() or q in d.name.lower() or (d.description and q in d.description.lower()):
                matched_domains.add(d.id)

    # 1. Search Objects
    for name, obj in registry.objects.items():
        is_match = (
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

    # 2. Search Actions
    for name, act in registry.actions.items():
        is_match = (
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
            if act.actor and act.actor.type in registry.objects:
                matched_obj_names.add(act.actor.type)

    # 3. Search Functions
    for name, fn in registry.functions.items():
        is_match = (
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

    # Graph expansion: Find links connecting matched objects
    for link in registry.links:
        if link.source in matched_obj_names or link.target in matched_obj_names:
            matched_obj_names.add(link.source)
            matched_obj_names.add(link.target)

    # Construct result details
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
                "preconditions": [p.model_dump(exclude_none=True) for p in act.preconditions],
                "effects": act.effects.model_dump(exclude_none=True) if act.effects else None,
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

    # Populate Rules that intersect with matched objects or query
    for r in registry.rules:
        if q in r.id.lower() or q in r.name.lower() or q in r.description.lower() or any(o in matched_obj_names for o in r.scope):
            result.rules.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "scope": r.scope,
                }
            )

    result.affected_files = sorted(list(affected_files))
    return result
