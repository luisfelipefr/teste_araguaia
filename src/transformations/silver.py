"""Limpeza e padronização dos dados para a camada Silver."""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path


def read_rows(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Lê um CSV preservando textos antes da tipagem."""
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            with file_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file, delimiter=";")
                rows = list(reader)
                return reader.fieldnames or [], rows
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler {file_path}")


def parse_brazil_number(value: str) -> str:
    """Converte número monetário brasileiro para texto decimal com ponto. R$"""
    cleaned = value.strip().replace(".", "").replace(",", ".")
    return f"{float(cleaned):.2f}"


def parse_date(value: str) -> str:
    cleaned = value.strip()
    for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"data inválida: {value}")


def choose_faturamento_files(input_directory: Path) -> list[Path]:
    """Escolhe a exportação mais recente para cada mês de exportação."""
    files = sorted(input_directory.glob("faturamento_export_*.csv"))
    selected: dict[str, Path] = {}
    for file_path in files:
        match = re.search(r"faturamento_export_(\d{6})\d{2}", file_path.name)
        if not match:
            raise ValueError(f"Nome de arquivo inválido: {file_path.name}")
        export_month = match.group(1)
        selected[export_month] = file_path
    return sorted(selected.values())


def normalize_faturamento(input_directory: Path, output_directory: Path) -> dict:
    """Normaliza faturamento, deduplica itens e persiste quarentena."""
    output_directory.mkdir(parents=True, exist_ok=True)
    selected_files = choose_faturamento_files(input_directory)
    valid_rows: list[dict[str, str]] = []
    quarantine_rows: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()

    for file_path in selected_files:
        columns, rows = read_rows(file_path)
        cost_column = "vlr_custo" if "vlr_custo" in columns else "valor_custo_total"
        for row in rows:
            row["source_file"] = file_path.name
            try:
                key = (row["nr_documento"].strip(), row["item"].strip())
                if not key[0] or not key[1] or key in seen_keys:
                    raise ValueError("chave nr_documento + item ausente ou duplicada")
                row["data_emissao"] = parse_date(row["data_emissao"])
                row["data_lancamento"] = parse_date(row["data_lancamento"])
                row["vlr_receita_liquida"] = parse_brazil_number(row["vlr_receita_liquida"])
                row["custo"] = parse_brazil_number(row[cost_column])
                row["competencia"] = row["data_lancamento"][:7]
                seen_keys.add(key)
                row.pop("vlr_custo", None)
                row.pop("valor_custo_total", None)
                valid_rows.append(row)
            except (KeyError, ValueError) as error:
                row["erro"] = str(error)
                quarantine_rows.append(row)

    output_columns = ordered_columns(valid_rows)
    quarantine_columns = ordered_columns(quarantine_rows)
    write_rows(output_directory / "faturamento.csv", output_columns, valid_rows)
    write_rows(output_directory / "quarantine_faturamento.csv", quarantine_columns, quarantine_rows)
    return {
        "selected_files": [path.name for path in selected_files],
        "valid_rows": len(valid_rows),
        "quarantine_rows": len(quarantine_rows),
    }


def normalize_clientes(input_directory: Path, output_directory: Path) -> int:
    """Limpa o cadastro e rejeita códigos de cliente repetidos ou vazios."""
    _, rows = read_rows(input_directory / "clientes.csv")
    valid_rows: list[dict[str, str]] = []
    quarantine_rows: list[dict[str, str]] = []
    seen_codes: set[str] = set()
    for row in rows:
        code = row.get("cod_cliente", "").strip()
        if not code or code in seen_codes:
            row["erro"] = "cod_cliente ausente ou duplicado"
            quarantine_rows.append(row)
            continue
        row["cod_cliente"] = code
        row["data_atribuicao_vendedor"] = parse_date(row["data_atribuicao_vendedor"])
        seen_codes.add(code)
        valid_rows.append(row)

    write_rows(output_directory / "clientes.csv", ordered_columns(valid_rows), valid_rows)
    write_rows(
        output_directory / "quarantine_clientes.csv",
        ordered_columns(quarantine_rows),
        quarantine_rows,
    )
    return len(valid_rows)


def write_rows(output_path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)


def ordered_columns(rows: list[dict[str, str]]) -> list[str]:
    """Retorna a união das colunas preservando a ordem da primeira ocorrência."""
    columns: list[str] = []
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)
    return columns


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = normalize_faturamento(
        project_root / "dados" / "entrada",
        project_root / "dados" / "silver",
    )
    result["clientes_validos"] = normalize_clientes(
        project_root / "dados" / "entrada",
        project_root / "dados" / "silver",
    )
    print(result)


if __name__ == "__main__":
    main()
