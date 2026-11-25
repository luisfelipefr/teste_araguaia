"""Orquestração local do pipeline Comercial."""

from __future__ import annotations

from pathlib import Path

from src.business.gold import build_gold, build_gold_clientes, run_metadata
from src.ingestion.bronze import ingest_to_bronze
from src.ingestion.inventory import build_inventory, write_inventory_report
from src.storage.sqlite_gold import create_gold_database
from src.transformations.silver import normalize_clientes, normalize_faturamento


def run_pipeline(project_root: Path) -> None:
    input_directory = project_root / "dados" / "entrada"
    bronze_directory = project_root / "dados" / "bronze"
    silver_directory = project_root / "dados" / "silver"
    gold_directory = project_root / "dados" / "gold"

    print("1/5 - Inventário")
    inventories = build_inventory(input_directory)
    write_inventory_report(inventories, project_root / "dados" / "inventario.json")

    print("2/5 - Bronze")
    ingest_to_bronze(input_directory, bronze_directory)

    print("3/5 - Silver")
    normalize_faturamento(input_directory, silver_directory)
    normalize_clientes(input_directory, silver_directory)

    print("4/5 - Gold")
    gold_run_id, processed_at = run_metadata()
    build_gold(
        silver_directory / "faturamento.csv",
        gold_directory,
        gold_run_id,
        processed_at,
    )
    build_gold_clientes(
        silver_directory / "faturamento.csv",
        silver_directory / "clientes.csv",
        gold_directory,
        gold_run_id,
        processed_at,
    )

    print("5/5 - SQLite")
    create_gold_database(gold_directory, gold_directory / "comercial.sqlite")
    print("Pipeline concluído")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    run_pipeline(project_root)


if __name__ == "__main__":
    main()
