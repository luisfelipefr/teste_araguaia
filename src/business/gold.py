"""Regras de negócio e geração das tabelas Gold do Comercial."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


def decimal_value(value: str) -> Decimal:
    return Decimal(value.strip())


def margin(revenue: Decimal, cost: Decimal) -> Decimal | None:
    if revenue == 0:
        return None
    return (revenue - cost) / revenue


def aggregate_rows(rows: list[dict[str, str]], dimensions: tuple[str, ...]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, ...], dict[str, object]] = {}
    for row in rows:
        key = tuple(row[dimension] for dimension in dimensions)
        group = grouped.setdefault(
            key,
            {
                **{dimension: row[dimension] for dimension in dimensions},
                "receita_total": Decimal("0"),
                "custo_total": Decimal("0"),
                "linhas_processadas": 0,
                "vendas": 0,
                "devolucoes": 0,
                "estornos": 0,
            },
        )
        group["receita_total"] += decimal_value(row["vlr_receita_liquida"])
        group["custo_total"] += decimal_value(row["custo"])
        group["linhas_processadas"] += 1
        tipo = row["tipo_documento"]
        if tipo == "VENDA":
            group["vendas"] += 1
        elif tipo == "DEVOLUCAO":
            group["devolucoes"] += 1
        elif tipo == "ESTORNO":
            group["estornos"] += 1

    result = []
    for group in grouped.values():
        revenue = group["receita_total"]
        cost = group["custo_total"]
        calculated_margin = margin(revenue, cost)
        result.append(
            {
                **{dimension: str(group[dimension]) for dimension in dimensions},
                "receita_total": f"{revenue:.2f}",
                "custo_total": f"{cost:.2f}",
                "margem": "" if calculated_margin is None else f"{calculated_margin:.8f}",
                "linhas_processadas": str(group["linhas_processadas"]),
                "vendas": str(group["vendas"]),
                "devolucoes": str(group["devolucoes"]),
                "estornos": str(group["estornos"]),
            }
        )
    return sorted(result, key=lambda item: tuple(item[dimension] for dimension in dimensions))


def read_silver(file_path: Path) -> list[dict[str, str]]:
    with file_path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def write_csv(file_path: Path, rows: list[dict[str, str]]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0].keys()) if rows else []
    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def build_gold(silver_path: Path, gold_directory: Path) -> dict[str, int]:
    rows = read_silver(silver_path)
    if not rows:
        raise ValueError("A Silver não possui linhas válidas")

    consultant_rows = aggregate_rows(
        rows,
        ("competencia", "cod_vendedor", "nome_vendedor"),
    )
    detail_rows = aggregate_rows(
        rows,
        ("competencia", "cod_vendedor", "nome_vendedor", "grupo_material"),
    )
    write_csv(gold_directory / "comercial_margem_consultor.csv", consultant_rows)
    write_csv(gold_directory / "comercial_margem_detalhada.csv", detail_rows)
    return {"consultor_rows": len(consultant_rows), "detail_rows": len(detail_rows)}


def build_gold_clientes(
    silver_faturamento_path: Path,
    silver_clientes_path: Path,
    gold_directory: Path,
) -> int:
    """Junta faturamento ao cadastro e agrega margem por cliente."""
    faturamento = read_silver(silver_faturamento_path)
    clientes = {row["cod_cliente"]: row for row in read_silver(silver_clientes_path)}
    enriched_rows: list[dict[str, str]] = []
    for row in faturamento:
        cliente = clientes.get(row["cod_cliente"])
        if cliente is None:
            continue
        enriched_rows.append(
            {
                **row,
                "nome_cliente": cliente["nome_cliente"],
                "segmento": cliente["segmento"],
            }
        )
    client_rows = aggregate_rows(
        enriched_rows,
        (
            "competencia",
            "cod_vendedor",
            "nome_vendedor",
            "cod_cliente",
            "nome_cliente",
            "segmento",
        ),
    )
    write_csv(gold_directory / "comercial_margem_cliente.csv", client_rows)
    return len(client_rows)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = build_gold(
        project_root / "dados" / "silver" / "faturamento.csv",
        project_root / "dados" / "gold",
    )
    client_rows = build_gold_clientes(
        project_root / "dados" / "silver" / "faturamento.csv",
        project_root / "dados" / "silver" / "clientes.csv",
        project_root / "dados" / "gold",
    )
    result["client_rows"] = client_rows
    print(result)


if __name__ == "__main__":
    main()
