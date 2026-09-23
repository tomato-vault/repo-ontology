"""Data models for repo-ontology."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CodeBindingBackend(BaseModel):
    model: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    service: Optional[str] = None
    api: Optional[str | List[str]] = None


class CodeBindingFrontend(BaseModel):
    entity: Optional[str] = None
    feature: Optional[str] = None
    page: Optional[str] = None


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
    range: Optional[List[int | float]] = None
    description: Optional[str] = None


class ObjectType(BaseModel):
    object: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    properties: Dict[str, PropertySpec | Dict[str, Any]] = Field(default_factory=dict)
    code_binding: Optional[CodeBinding] = None


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


class ActorSpec(BaseModel):
    type: str
    role: Optional[str | List[str]] = None
    permission: Optional[str] = None


class TargetSpec(BaseModel):
    object: str
    lookup: str = "id"


class PreconditionSpec(BaseModel):
    id: Optional[str] = None
    rule: str
    error: str


class SideEffects(BaseModel):
    mutate: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None


class GovernanceSpec(BaseModel):
    feature_id: Optional[str] = None
    adr: Optional[str] = None
    tech_debt: Optional[str] = None


class ActionType(BaseModel):
    action: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    actor: Optional[ActorSpec] = None
    target: Optional[TargetSpec] = None
    parameters: Dict[str, PropertySpec | Dict[str, Any]] = Field(default_factory=dict)
    preconditions: List[PreconditionSpec] = Field(default_factory=list)
    effects: Optional[SideEffects] = None
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


class RuleTypeDoc(BaseModel):
    rules: List[RuleSpec] = Field(default_factory=list)


class DomainConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class StackConfig(BaseModel):
    backend: Optional[Dict[str, Any]] = None
    frontend: Optional[Dict[str, Any]] = None
    mobile: Optional[Dict[str, Any]] = None


class GovernanceConfig(BaseModel):
    adr_dir: Optional[str] = "docs/adr"
    tech_debt_file: Optional[str] = "docs/tech-debt.md"
    watchlist_file: Optional[str] = "docs/deferred-watchlist.md"


class OntologyConfig(BaseModel):
    version: str = "1.0.0"
    project: Optional[Dict[str, Any]] = None
    stack: Optional[StackConfig] = None
    domains: List[DomainConfig] = Field(default_factory=list)
    governance: Optional[GovernanceConfig] = None
