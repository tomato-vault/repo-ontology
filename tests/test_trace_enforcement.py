from pathlib import Path
from repo_ontology.loader import load_ontology
from repo_ontology.trace import trace_ontology
from repo_ontology.loader import OntologyRegistry
from repo_ontology.models import ObjectType, RuleSpec


def test_trace_rule_enforcement_files():
    # Test that tracing a rule extracts enforcement code paths
    template_dir = Path(__file__).resolve().parent.parent / "template"
    registry = load_ontology(template_dir)

    # In template, find rules or trace by query
    res = trace_ontology(registry, "attendance")
    assert len(res.affected_files) > 0
    assert any("attendance" in f.lower() for f in res.affected_files)


def test_rule_spec_has_enforcement_field():
    from repo_ontology.models import RuleSpec
    rule = RuleSpec(
        id="TEST_RULE",
        name="Test Invariant",
        description="Testing enforcement extraction",
        scope=["User"],
        enforcement={
            "code": ["backend/app/services/test_service.py:test_fn"],
            "tests": ["tests/test_something.py"]
        }
    )
    assert rule.enforcement is not None
    assert "code" in rule.enforcement
    assert "backend/app/services/test_service.py:test_fn" in rule.enforcement["code"]


def test_exact_rule_id_does_not_expand_to_unrelated_rules(tmp_path):
    registry = OntologyRegistry(tmp_path, tmp_path / ".ontology")
    registry.objects["Billing"] = ObjectType(object="Billing", description="Billing")
    registry.rules = [
        RuleSpec(id="OVER_REFUND", name="Refund", description="Refund guard", scope=["Billing"],
                 enforcement={"guard": "backend/refund.py:check"}),
        RuleSpec(id="OTHER_RULE", name="Other", description="Other guard", scope=["Billing"],
                 enforcement={"guard": "backend/other.py:check"}),
    ]

    result = trace_ontology(registry, "OVER_REFUND")
    assert [rule["id"] for rule in result.rules] == ["OVER_REFUND"]
    assert result.affected_files == ["backend/refund.py"]
