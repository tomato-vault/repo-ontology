from pathlib import Path
from repo_ontology.loader import load_ontology

def test_load_template_ontology():
    template_dir = Path(__file__).resolve().parent.parent / "template"
    registry = load_ontology(template_dir)

    assert not registry.has_errors
    assert "User" in registry.objects
    assert "Course" in registry.objects
    assert "AssignmentSubmission" in registry.objects
    assert "ClassSession" in registry.objects
    assert len(registry.links) >= 4
    assert "GradeSubmission" in registry.actions
    assert "RecordAttendance" in registry.actions
    assert "CalculateAttendanceRate" in registry.functions
    assert len(registry.rules) >= 2
