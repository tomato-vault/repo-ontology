from pathlib import Path
from repo_ontology.loader import load_ontology
from repo_ontology.trace import trace_ontology

def test_trace_attendance():
    template_dir = Path(__file__).resolve().parent.parent / "template"
    registry = load_ontology(template_dir)
    res = trace_ontology(registry, "attendance")

    obj_names = [o["name"] for o in res.objects]
    action_names = [a["name"] for a in res.actions]
    func_names = [f["name"] for f in res.functions]

    assert "ClassSession" in obj_names
    assert "RecordAttendance" in action_names
    assert "CalculateAttendanceRate" in func_names
    assert len(res.affected_files) > 0
    assert "backend/app/services/attendance_service.py" in res.affected_files
