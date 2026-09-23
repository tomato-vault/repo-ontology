from repo_ontology.cli import main


def test_info_and_trace_fail_on_invalid_ontology(tmp_path, capsys):
    rule_dir = tmp_path / ".ontology" / "rules"
    rule_dir.mkdir(parents=True)
    (rule_dir / "bad.yml").write_text(
        "rules:\n  - id: R\n    name: R\n    description: rule\n    enforcment: missing.py\n"
    )

    assert main(["info", str(tmp_path)]) == 1
    assert main(["trace", "R", str(tmp_path), "--json"]) == 1
    output = capsys.readouterr()
    assert "enforcment" in output.err
    assert "Ontology Overview" not in output.out
