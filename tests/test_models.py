import pytest
from pydantic import ValidationError

from repo_ontology.models import ObjectType, RuleSpec


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (RuleSpec, {"id": "R", "name": "R", "description": "rule", "enforcment": "missing.py"}),
        (ObjectType, {"object": "O", "description": "object", "constrants": []}),
        (ObjectType, {
            "object": "O", "description": "object",
            "code_binding": {"backend": {"reqest_schema": "missing.py"}},
        }),
        (ObjectType, {
            "object": "O", "description": "object",
            "properties": {"amount": {"type": "integer", "requred": True}},
        }),
    ],
)
def test_unknown_ontology_fields_are_rejected(model, payload):
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        model.model_validate(payload)


def test_rule_enforcement_rejects_non_path_values():
    with pytest.raises(ValidationError, match="enforcement entries must be non-empty code paths"):
        RuleSpec.model_validate({
            "id": "R", "name": "R", "description": "rule",
            "enforcement": {"service": {"code": 123}},
        })
