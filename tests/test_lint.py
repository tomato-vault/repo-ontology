from pathlib import Path
from repo_ontology.loader import load_ontology
from repo_ontology.lint import lint_ontology
from repo_ontology.loader import OntologyRegistry
from repo_ontology.models import ActionType

def test_lint_template_skipping_code():
    template_dir = Path(__file__).resolve().parent.parent / "template"
    registry = load_ontology(template_dir)
    issues = lint_ontology(registry, check_code=False)

    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 0


def test_lint_checks_nested_and_additional_code_bindings(tmp_path):
    registry = OntologyRegistry(tmp_path, tmp_path / ".ontology")
    registry.actions["Example"] = ActionType.model_validate({
        "action": "Example",
        "description": "Check every binding",
        "code_binding": {
            "backend": {"request_schema": "missing/request.py:Request"},
            "frontend": {"ui": {"modal": "missing/Modal.jsx"}},
        },
    })

    issues = lint_ontology(registry, strict_code=True)
    assert len(issues) == 2
    assert all(issue.severity == "ERROR" for issue in issues)
    assert {issue.location for issue in issues} == {
        "Action 'Example'.backend.request_schema",
        "Action 'Example'.frontend.ui.modal",
    }
