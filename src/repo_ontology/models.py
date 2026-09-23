"""Data models for repo-ontology."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class CodeBindingBackend(BaseModel):
    model: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    service: Optional[str] = None
    api: Optional[Union[str, List[str]]] = None
    stats_service: Optional[str] = None
    background_task: Optional[str] = None


class CodeBindingFrontend(BaseModel):
    entity: Optional[str] = None
    feature: Optional[str] = None
    page: Optional[str] = None
    api: Optional[Union[str, List[str]]] = None
    model: Optional[str] = None
    hook: Optional[str] = None


class CodeBindingMobile(BaseModel):
    model: Optional[str] = None
    viewmodel: Optional[str] = None
    page: Optional[str] = None


class CodeBinding(BaseModel):
    backend: Optional[CodeBindingBackend] = None
    frontend: Optional[CodeBindingFrontend] = None
    mobile: Optional[CodeBindingMobile] = None


class PropertySpec(BaseModel):
    type: str
    required: bool = False
    unique: bool = False
    primary_key: bool = False
    default: Optional[Any] = None
    nullable: bool = False
    values: Optional[List[str]] = None
    range: Optional[List[Union[int, float]]] = None
    description: Optional[str] = None
    max_length: Optional[int] = None
    foreign_key: Optional[str] = None
    check: Optional[str] = None
    items: Optional[str] = None
    auto_now: Optional[bool] = None
    auto_now_add: Optional[bool] = None
    index: Optional[bool] = None


class ActorSpec(BaseModel):
    type: str
    role: Optional[Union[str, List[str]]] = None
    roles: List[str] = Field(default_factory=list)
    permission: Optional[str] = None
    context: Optional[str] = None


class TargetSpec(BaseModel):
    object: str
    lookup: str = "id"


class PreconditionSpec(BaseModel):
    id: Optional[str] = None
    rule: Optional[str] = None
    rule_id: Optional[str] = None
    expression: Optional[str] = None
    error: Optional[str] = None


class SideEffects(BaseModel):
    mutate: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None


class GovernanceSpec(BaseModel):
    feature_id: Optional[str] = None
    adr: Optional[str] = None
    tech_debt: Optional[str] = None


class ObjectType(BaseModel):
    object: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    properties: Dict[str, Union[PropertySpec, Dict[str, Any]]] = Field(default_factory=dict)
    code_binding: Optional[CodeBinding] = None
    constraints: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    computed_properties: Union[Dict[str, Any], List[str]] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    enums: Dict[str, List[str]] = Field(default_factory=dict)
    actor: Optional[ActorSpec] = None


class LinkSpec(BaseModel):
    name: str
    source: str
    target: str
    cardinality: str  # one_to_one | one_to_many | many_to_one | many_to_many
    through: Optional[str] = None
    foreign_key: Optional[str] = None
    description: Optional[str] = None


class LinkTypeDoc(BaseModel):
    links: List[LinkSpec] = Field(default_factory=list)


class ActionType(BaseModel):
    action: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    actor: Optional[ActorSpec] = None
    target: Optional[TargetSpec] = None
    parameters: Dict[str, Union[PropertySpec, Dict[str, Any]]] = Field(default_factory=dict)
    preconditions: List[Union[PreconditionSpec, Dict[str, Any]]] = Field(default_factory=list)
    effects: Optional[SideEffects] = None
    effect: Optional[Any] = None
    request_schema: Optional[str] = None
    background_task: Optional[bool] = False
    stats_service: Optional[str] = None
    code_binding: Optional[CodeBinding] = None
    governance: Optional[GovernanceSpec] = None


class FunctionType(BaseModel):
    function: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    computation: Optional[Dict[str, Any]] = None
    code_binding: Optional[CodeBinding] = None


class RuleSpec(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    description: str
    scope: List[str] = Field(default_factory=list)
    enforcement: Optional[Union[Dict[str, List[str]], List[str], str]] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    expression: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RuleTypeDoc(BaseModel):
    rules: List[RuleSpec] = Field(default_factory=list)


class DomainConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class ProjectInfo(BaseModel):
    name: str = "My Project"
    description: Optional[str] = None
    repository_url: Optional[str] = None


class StackComponent(BaseModel):
    framework: Optional[str] = None
    root: Optional[str] = None
    architecture: Optional[str] = None


class StackConfig(BaseModel):
    backend: Optional[Union[StackComponent, str]] = None
    frontend: Optional[Union[StackComponent, str]] = None
    mobile: Optional[Union[StackComponent, str]] = None
    database: Optional[str] = None


class GovernanceConfig(BaseModel):
    adr_dir: Optional[str] = "docs/adr"
    tech_debt_file: Optional[str] = None
    watchlist_file: Optional[str] = None


class OntologyConfig(BaseModel):
    version: str = "1.0.0"
    name: Optional[str] = None
    project: Optional[Union[ProjectInfo, str]] = None
    domains: List[DomainConfig] = Field(default_factory=list)
    stack: Optional[StackConfig] = None
    governance: Optional[GovernanceConfig] = None
