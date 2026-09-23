"""Scaffold new ontology elements."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def to_kebab_case(s: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", s)
    return s.replace("_", "-").lower()


def scaffold_element(
    element_type: str,
    name: str,
    domain: Optional[str] = "core",
    ontology_dir: Optional[Path] = None,
) -> Path:
    """Generate a template YAML file for a new Object, Action, or Function."""
    from repo_ontology.loader import find_ontology_dir

    onto_dir = ontology_dir or find_ontology_dir()
    if onto_dir is None:
        raise FileNotFoundError("Could not find '.ontology' directory.")

    file_name = f"{to_kebab_case(name)}.yml"

    if element_type.lower() in ("object", "obj"):
        target_file = onto_dir / "objects" / file_name
        content = f"""object: {name}
domain: "{domain}"
tags: ["{to_kebab_case(name)}"]
description: "{name} 도메인 엔티티 설명"

properties:
  id:
    type: uuid
    primary_key: true
  created_at:
    type: datetime
    required: true

code_binding:
  backend:
    model: "backend/app/models/{to_kebab_case(name)}.py:{name}"
    schema: "backend/app/schemas/{to_kebab_case(name)}.py:{name}Schema"
  frontend:
    entity: "frontend/src/entities/{to_kebab_case(name)}"
"""
    elif element_type.lower() in ("action", "act"):
        target_file = onto_dir / "actions" / file_name
        content = f"""action: {name}
domain: "{domain}"
tags: ["{to_kebab_case(name)}"]
description: "{name} 상태 변경 트랜잭션 설명"

actor:
  type: User
  role: "USER"

target:
  object: TargetObject
  lookup: "id"

parameters:
  param1:
    type: string
    required: true

preconditions:
  - id: "VALID_STATE"
    rule: "target.status == 'ACTIVE'"
    error: "활성화 상태에서만 실행할 수 있습니다."

effects:
  mutate:
    target.updated_at: "now()"

code_binding:
  backend:
    service: "backend/app/services/{to_kebab_case(name)}_service.py:{to_kebab_case(name)}"
  frontend:
    feature: "frontend/src/features/{to_kebab_case(name)}"
"""
    elif element_type.lower() in ("function", "func", "fn"):
        target_file = onto_dir / "functions" / file_name
        content = f"""function: {name}
domain: "{domain}"
tags: ["{to_kebab_case(name)}", "calculation"]
description: "{name} 순수 도출 및 계산 로직 설명"

inputs:
  target_id:
    type: uuid
    required: true

output:
  type: object
  properties:
    result: {{ type: float }}

computation:
  formula: "target.value * 1.0"

code_binding:
  backend:
    service: "backend/app/services/{to_kebab_case(name)}_service.py:calculate_{to_kebab_case(name)}"
"""
    else:
        raise ValueError(f"Unknown element type: '{element_type}'. Supported: object, action, function.")

    target_file.parent.mkdir(parents=True, exist_ok=True)
    if target_file.exists():
        raise FileExistsError(f"File already exists: {target_file}")

    target_file.write_text(content, encoding="utf-8")
    return target_file
