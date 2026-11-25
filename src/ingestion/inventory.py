"""Inventário dos arquivos CSV recebidos na entrada."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


ENCODINGS_TO_TRY = ("utf-8-sig", "utf-8", "latin1")


@dataclass
class FileInventory:
    """Resumo estrutural de um arquivo CSV."""

    file_name: str
    file_path: str
    encoding: str
    delimiter: str
    row_count: int
    column_count: int
    columns: list[str]


def read_csv_inventory(file_path: Path) -> FileInventory:
    """Lê o cabeçalho e conta as linhas de um CSV sem carregar tudo na memória."""
    last_error: UnicodeDecodeError | None = None

    for encoding in ENCODINGS_TO_TRY:
        try:
            with file_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.reader(file, delimiter=";")
                columns = next(reader, [])
                row_count = sum(1 for _ in reader)
            break
        except UnicodeDecodeError as error:
            last_error = error
    else:
        raise ValueError(f"Não foi possível ler {file_path}") from last_error

    return FileInventory(
        file_name=file_path.name,
        file_path=str(file_path),
        encoding=encoding,
        delimiter=";",
        row_count=row_count,
        column_count=len(columns),
        columns=columns,
    )


def build_inventory(input_directory: Path) -> list[FileInventory]:
    """Cria o inventário de todos os CSVs da pasta de entrada."""
    files = sorted(input_directory.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {input_directory}")
    return [read_csv_inventory(file_path) for file_path in files]


def find_schema_differences(inventories: list[FileInventory]) -> dict[str, list[str]]:
    """Compara as colunas dos arquivos e retorna as diferenças em relação ao primeiro."""
    """EXEMPLO:  vlr_custo e valor_custo_total"""
    reference_columns = set(inventories[0].columns)
    differences: dict[str, list[str]] = {}

    for inventory in inventories[1:]:
        columns = set(inventory.columns)
        missing = sorted(reference_columns - columns)
        extra = sorted(columns - reference_columns)
        if missing or extra:
            differences[inventory.file_name] = [
                f"ausentes: {missing}",
                f"adicionadas: {extra}",
            ]

    return differences


def write_inventory_report(
    inventories: list[FileInventory],
    output_path: Path,
) -> None:
    """Grava o inventário e as diferenças de esquema em JSON."""
    report = {
        "files": [asdict(inventory) for inventory in inventories],
        "schema_differences": find_schema_differences(inventories),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    input_directory = project_root / "dados" / "entrada"
    output_path = project_root / "dados" / "inventario.json"

    inventories = build_inventory(input_directory)
    write_inventory_report(inventories, output_path)

    for inventory in inventories:
        print(
            f"{inventory.file_name}: {inventory.row_count} linhas, "
            f"{inventory.column_count} colunas, encoding={inventory.encoding}"
        )
    print(f"Relatório gravado em: {output_path}")


if __name__ == "__main__":
    main()
