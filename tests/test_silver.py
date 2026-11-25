from pathlib import Path

from src.transformations.silver import choose_faturamento_files, normalize_faturamento


INPUT_DIRECTORY = Path(__file__).parents[1] / "dados" / "entrada"


def test_silver_selects_latest_export_for_october() -> None:
    selected = choose_faturamento_files(INPUT_DIRECTORY)

    assert "faturamento_export_20261105.csv" in [path.name for path in selected]
    assert "faturamento_export_20261103.csv" not in [path.name for path in selected]


def test_silver_normalizes_faturamento(tmp_path: Path) -> None:
    result = normalize_faturamento(INPUT_DIRECTORY, tmp_path)

    assert result["valid_rows"] > 0
    assert result["quarantine_rows"] >= 0
    assert (tmp_path / "faturamento.csv").exists()
    assert (tmp_path / "quarantine_faturamento.csv").exists()

# python -m src.transformations.silver