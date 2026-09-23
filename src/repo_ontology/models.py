"""Data models for repo-ontology."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OntologyModel(BaseModel):
    """Reject misspelled ontology fields instead of silently discarding them."""

    model_config = ConfigDict(extra="forbid")


class CodeBindingBackend(OntologyModel):
    model: Optional[str] = None
    alias: Optional[str] = None
    adjustment_model: Optional[str] = None
    enum: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    crud: Optional[str] = None
    service: Optional[str] = None
    bulk_service: Optional[str] = None
    router: Optional[str] = None
    api: Optional[Union[str, List[str]]] = None
    parent_api: Optional[str] = None
    bulk_api: Optional[str] = None
    stats_service: Optional[str] = None
    pure_function: Optional[str] = None
    background_task: Optional[str] = None
    request_schema: Optional[str] = None


class CodeBindingFrontend(OntologyModel):
    entity: Optional[str] = None
    feature: Optional[str] = None
    page: Optional[str] = None
    api: Optional[Union[str, List[str]]] = None
    model: Optional[str] = None
    hook: Optional[str] = None
    service: Optional[str] = None
    ui: Optional[Union[str, Dict[str, str]]] = None
    constants: Optional[str] = None
    options: Optional[str] = None
    bulk_api: Optional[str] = None


class CodeBindingMobile(OntologyModel):
    model: Optional[str] = None
    viewmodel: Optional[str] = None
    page: Optional[str] = None
    repository: Optional[str] = None
    view: Optional[str] = None


class CodeBinding(OntologyModel):
    backend: Optional[CodeBindingBackend] = None
    frontend: Optional[CodeBindingFrontend] = None
    mobile: Optional[CodeBindingMobile] = None


class PropertySpec(OntologyModel):
    type: Optional[str] = None
    required: bool = False
    unique: bool = False
    primary_key: bool = False
    default: Optional[Any] = None
    nullable: bool = False
    values: Optional[List[Union[str, int, float]]] = None
    range: Optional[List[Union[int, float]]] = None
    description: Optional[str] = None
    max_length: Optional[int] = None
    foreign_key: Optional[str] = None
    check: Optional[str] = None
    items: Optional[Union[str, Dict[str, Any]]] = None
    auto_now: Optional[bool] = None
    auto_now_add: Optional[bool] = None
    index: Optional[bool] = None
    fields: Optional[Dict[str, "PropertySpec"]] = None
    schema_: Optional[Dict[str, Any]] = Field(default=None, alias="schema")
    model: Optional[str] = None
    table: Optional[str] = None
    timezone: Optional[bool] = None
    format: Optional[str] = None
    min_items: Optional[int] = None
    min_value: Optional[Union[int, float]] = None

    @model_validator(mode="after")
    def require_type_or_group(self) -> "PropertySpec":
        if self.type is None and self.fields is None and self.model is None:
            raise ValueError("property requires type, fields, or model")
        return self


class ActorSpec(OntologyModel):
    type: str
    role: Optional[Union[str, List[str]]] = None
    roles: List[str] = Field(default_factory=list)
    permission: Optional[str] = None
    context: Optional[str] = None


class TargetSpec(OntologyModel):
    object: str
    lookup: str = "id"


class PreconditionSpec(OntologyModel):
    id: Optional[str] = None
    rule: Optional[str] = None
    rule_id: Optional[str] = None
    expression: Optional[str] = None
    error: Optional[str] = None


class SideEffects(OntologyModel):
    mutate: Optional[Dict[str, Any]] = None
    events: Optional[List[Dict[str, Any]]] = None
    read_derivation: Optional[Dict[str, Any]] = None


class GovernanceSpec(OntologyModel):
    feature_id: Optional[str] = None
    adr: Optional[str] = None
    tech_debt: Optional[str] = None
    docs: Optional[str] = None
    feature_doc: Optional[str] = None


class ObjectType(OntologyModel):
    object: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    properties: Dict[str, PropertySpec] = Field(default_factory=dict)
    code_binding: Optional[CodeBinding] = None
    constraints: Union[Dict[str, Any], List[Any]] = Field(default_factory=list)
    computed_properties: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    relationships: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    relations: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    related_objects: Dict[str, Any] = Field(default_factory=dict)
    enums: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    actor: Optional[ActorSpec] = None
    governance: Optional[GovernanceSpec] = None


class LinkSpec(OntologyModel):
    name: str
    source: str
    target: str
    cardinality: str  # one_to_one | one_to_many | many_to_one | many_to_many
    through: Optional[str] = None
    foreign_key: Optional[str] = None
    description: Optional[str] = None


class LinkTypeDoc(OntologyModel):
    links: List[LinkSpec] = Field(default_factory=list)


class ActionType(OntologyModel):
    action: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    actor: Optional[ActorSpec] = None
    target: Optional[TargetSpec] = None
    parameters: Dict[str, PropertySpec] = Field(default_factory=dict)
    preconditions: List[Union[PreconditionSpec, Dict[str, Any]]] = Field(default_factory=list)
    effects: Optional[SideEffects] = None
    effect: Optional[Any] = None
    request_schema: Optional[str] = None
    background_task: Optional[bool] = False
    stats_service: Optional[str] = None
    code_binding: Optional[CodeBinding] = None
    governance: Optional[GovernanceSpec] = None


class FunctionType(OntologyModel):
    function: str
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    computation: Optional[Dict[str, Any]] = None
    code_binding: Optional[CodeBinding] = None


class RuleSpec(OntologyModel):
    id: str
    name: str
    domain: Optional[str] = None
    description: str
    scope: List[str] = Field(default_factory=list)
    enforcement: Optional[Union[Dict[str, Any], List[str], str]] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    expression: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("enforcement")
    @classmethod
    def require_enforcement_paths(cls, value):
        def check_paths(item):
            if isinstance(item, dict):
                for nested in item.values():
                    check_paths(nested)
            elif isinstance(item, list):
                for nested in item:
                    check_paths(nested)
            elif not isinstance(item, str) or not item.strip():
                raise ValueError("enforcement entries must be non-empty code paths")

        if value is not None:
            check_paths(value)
        return value


class RuleTypeDoc(OntologyModel):
    rules: List[RuleSpec] = Field(default_factory=list)


class DomainConfig(OntologyModel):
    id: str
    name: str
    description: Optional[str] = None


class ProjectInfo(OntologyModel):
    name: str = "My Project"
    description: Optional[str] = None
    repository_url: Optional[str] = None


class StackComponent(OntologyModel):
    framework: Optional[str] = None
    root: Optional[str] = None
    architecture: Optional[str] = None


class StackConfig(OntologyModel):
    backend: Optional[Union[StackComponent, str]] = None
    frontend: Optional[Union[StackComponent, str]] = None
    mobile: Optional[Union[StackComponent, str]] = None
    database: Optional[str] = None


class GovernanceConfig(OntologyModel):
    adr_dir: Optional[str] = "docs/adr"
    tech_debt_file: Optional[str] = None
    watchlist_file: Optional[str] = None


class OntologyConfig(OntologyModel):
    version: str = "1.0.0"
    name: Optional[str] = None
    project: Optional[Union[ProjectInfo, str]] = None
    domains: List[DomainConfig] = Field(default_factory=list)
    stack: Optional[StackConfig] = None
    governance: Optional[GovernanceConfig] = None
