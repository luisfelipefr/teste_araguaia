import sqlite3
from pathlib import Path

from src.storage.sqlite_gold import create_gold_database


GOLD_DIRECTORY = Path(__file__).parents[1] / "dados" / "gold"


def test_sqlite_contains_gold_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "comercial.sqlite"
    create_gold_database(GOLD_DIRECTORY, database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert "comercial_margem_consultor" in tables
        assert "comercial_margem_detalhada" in tables
        assert "comercial_margem_cliente" in tables

        count = connection.execute(
            "SELECT COUNT(*) FROM comercial_margem_consultor"
        ).fetchone()[0]
        assert count > 0
