from pathlib import Path

from src.pipeline import run_pipeline


def test_pipeline_creates_gold_database(tmp_path: Path) -> None:
    project_root = tmp_path
    input_directory = project_root / "dados" / "entrada"
    source_directory = Path(__file__).parents[1] / "dados" / "entrada"
    input_directory.mkdir(parents=True)
    for source_file in source_directory.glob("*.csv"):
        (input_directory / source_file.name).write_bytes(source_file.read_bytes())

    run_pipeline(project_root)

    assert (project_root / "dados" / "gold" / "comercial.sqlite").exists()
