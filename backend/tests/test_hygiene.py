from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_schema_definitions_are_unique() -> None:
    schemas_path = ROOT / "backend" / "app" / "api" / "schemas.py"
    tree = ast.parse(schemas_path.read_text(encoding="utf-8"))
    class_names: list[str] = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    duplicates = [name for name in set(class_names) if class_names.count(name) > 1]
    assert not duplicates, f"Duplicate class definitions found in schemas.py: {duplicates}"


def test_config_secret_key_loaded() -> None:
    from app.core import config
    assert hasattr(config, "SECRET_KEY"), "config.py must define SECRET_KEY"
    assert config.SECRET_KEY, "SECRET_KEY must not be empty"


def test_fixture_structure_cleanliness() -> None:
    fixtures_dir = ROOT / "evaluation" / "fixtures" / "pdfs"
    loose_pdfs = list(fixtures_dir.glob("*.pdf"))
    assert not loose_pdfs, f"Found loose PDF files in {fixtures_dir}: {[p.name for p in loose_pdfs]}"

    subdirs = [p for p in fixtures_dir.iterdir() if p.is_dir()]
    assert len(subdirs) >= 3, f"Expected at least 3 labeled notice subdirectories, found {len(subdirs)}"
    for subdir in subdirs:
        pdf_files = list(subdir.glob("*.pdf"))
        expected_files = list(subdir.glob("expected.json"))
        assert len(pdf_files) == 1, f"{subdir.name} must contain exactly one .pdf file"
        assert len(expected_files) == 1, f"{subdir.name} must contain exactly one expected.json file"

