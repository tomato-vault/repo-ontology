from pathlib import Path
from repo_ontology.loader import load_ontology
from repo_ontology.lint import lint_ontology

def test_lint_template_skipping_code():
    template_dir = Path(__file__).resolve().parent.parent / "template"
    registry = load_ontology(template_dir)
    issues = lint_ontology(registry, check_code=False)

    errors = [i for i in issues if i.severity == "ERROR"]
    assert len(errors) == 0
