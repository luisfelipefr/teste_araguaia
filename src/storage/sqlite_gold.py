"""Persistência local das tabelas Gold em SQLite."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


CONSULTANT_COLUMNS = (
    "competencia",
    "cod_vendedor",
    "nome_vendedor",
    "receita_total",
    "custo_total",
    "margem",
    "linhas_processadas",
    "vendas",
    "devolucoes",
    "estornos",
)

DETAIL_COLUMNS = (
    "competencia",
    "cod_vendedor",
    "nome_vendedor",
    "grupo_material",
    "receita_total",
    "custo_total",
    "margem",
    "linhas_processadas",
    "vendas",
    "devolucoes",
    "estornos",
)

CLIENT_COLUMNS = (
    "competencia",
    "cod_vendedor",
    "nome_vendedor",
    "cod_cliente",
    "nome_cliente",
    "segmento",
    "receita_total",
    "custo_total",
    "margem",
    "linhas_processadas",
    "vendas",
    "devolucoes",
    "estornos",
)


def read_csv(file_path: Path) -> list[dict[str, str]]:
    with file_path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def create_gold_database(gold_directory: Path, database_path: Path) -> None:
    consultant_rows = read_csv(gold_directory / "comercial_margem_consultor.csv")
    detail_rows = read_csv(gold_directory / "comercial_margem_detalhada.csv")
    client_rows = read_csv(gold_directory / "comercial_margem_cliente.csv")
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS comercial_margem_consultor;
            DROP TABLE IF EXISTS comercial_margem_detalhada;
            DROP TABLE IF EXISTS comercial_margem_cliente;

            CREATE TABLE comercial_margem_consultor (
                competencia TEXT NOT NULL,
                cod_vendedor TEXT NOT NULL,
                nome_vendedor TEXT NOT NULL,
                receita_total REAL NOT NULL,
                custo_total REAL NOT NULL,
                margem REAL,
                linhas_processadas INTEGER NOT NULL,
                vendas INTEGER NOT NULL,
                devolucoes INTEGER NOT NULL,
                estornos INTEGER NOT NULL,
                PRIMARY KEY (competencia, cod_vendedor)
            );

            CREATE TABLE comercial_margem_detalhada (
                competencia TEXT NOT NULL,
                cod_vendedor TEXT NOT NULL,
                nome_vendedor TEXT NOT NULL,
                grupo_material TEXT NOT NULL,
                receita_total REAL NOT NULL,
                custo_total REAL NOT NULL,
                margem REAL,
                linhas_processadas INTEGER NOT NULL,
                vendas INTEGER NOT NULL,
                devolucoes INTEGER NOT NULL,
                estornos INTEGER NOT NULL,
                PRIMARY KEY (competencia, cod_vendedor, grupo_material)
            );

            CREATE TABLE comercial_margem_cliente (
                competencia TEXT NOT NULL,
                cod_vendedor TEXT NOT NULL,
                nome_vendedor TEXT NOT NULL,
                cod_cliente TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,
                segmento TEXT NOT NULL,
                receita_total REAL NOT NULL,
                custo_total REAL NOT NULL,
                margem REAL,
                linhas_processadas INTEGER NOT NULL,
                vendas INTEGER NOT NULL,
                devolucoes INTEGER NOT NULL,
                estornos INTEGER NOT NULL,
                PRIMARY KEY (competencia, cod_vendedor, cod_cliente)
            );
            """
        )
        connection.executemany(
            """
            INSERT INTO comercial_margem_consultor VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [tuple(convert_value(row[column]) for column in CONSULTANT_COLUMNS) for row in consultant_rows],
        )
        connection.executemany(
            """
            INSERT INTO comercial_margem_detalhada VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [tuple(convert_value(row[column]) for column in DETAIL_COLUMNS) for row in detail_rows],
        )
        connection.executemany(
            "INSERT INTO comercial_margem_cliente VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [tuple(convert_value(row[column]) for column in CLIENT_COLUMNS) for row in client_rows],
        )
        connection.commit()


def convert_value(value: str) -> str | int | float | None:
    if value == "":
        return None
    if "." in value and value.replace(".", "", 1).replace("-", "", 1).isdigit():
        return float(value)
    if value.isdigit():
        return int(value)
    return value


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    database_path = project_root / "dados" / "gold" / "comercial.sqlite"
    create_gold_database(project_root / "dados" / "gold", database_path)
    print(f"Banco Gold criado em: {database_path}")


if __name__ == "__main__":
    main()
