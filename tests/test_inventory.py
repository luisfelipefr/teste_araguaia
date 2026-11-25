from pathlib import Path

from src.ingestion.inventory import build_inventory, find_schema_differences


INPUT_DIRECTORY = Path(__file__).parents[1] / "dados" / "entrada"


def test_inventory_finds_received_csv_files() -> None:
    inventories = build_inventory(INPUT_DIRECTORY)

    assert len(inventories) == 5
    assert {inventory.file_name for inventory in inventories} == {
        "clientes.csv",
        "faturamento_export_20260902.csv",
        "faturamento_export_20261002.csv",
        "faturamento_export_20261103.csv",
        "faturamento_export_20261105.csv",
    }


def test_inventory_detects_october_schema_change() -> None:
    inventories = build_inventory(INPUT_DIRECTORY)
    differences = find_schema_differences(inventories)

    assert "faturamento_export_20261103.csv" in differences
    assert "faturamento_export_20261105.csv" in differences

# python -m src.ingestion.inventory