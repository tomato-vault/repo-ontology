import tempfile
from pathlib import Path
from repo_ontology.init import init_project

def test_init_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        dest = init_project(tmp_path)

        assert dest.is_dir()
        assert (dest / "config.yml").is_file()
        assert (dest / "objects" / "user.yml").is_file()
        assert (dest / "actions" / "grade-submission.yml").is_file()
        assert (dest / "functions" / "calculate-attendance-rate.yml").is_file()
