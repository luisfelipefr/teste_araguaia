import json
from pathlib import Path

from src.ingestion.bronze import ingest_to_bronze


INPUT_DIRECTORY = Path(__file__).parents[1] / "dados" / "entrada"


def test_bronze_copies_all_files_and_creates_manifest(tmp_path: Path) -> None:
    bronze_directory = tmp_path / "bronze"

    manifest = ingest_to_bronze(INPUT_DIRECTORY, bronze_directory)

    assert len(manifest["files"]) == 5
    assert {file["domain"] for file in manifest["files"]} == {
        "clientes",
        "faturamento",
    }

    manifest_path = bronze_directory / "manifests" / f"{manifest['run_id']}.json"
    assert manifest_path.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["run_id"] == manifest[
        "run_id"
    ]

    for file_metadata in manifest["files"]:
        assert Path(file_metadata["bronze_path"]).exists()
        
# python -m src.ingestion.bronze