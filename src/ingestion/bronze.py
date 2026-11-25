"""Ingestão dos arquivos recebidos na camada Bronze."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - compatibilidade com versões antigas
    ZoneInfo = None


def count_rows(file_path: Path) -> int:
    """Conta linhas de um CSV sem alterar nem carregar o arquivo inteiro."""
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            with file_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.reader(file, delimiter=";")
                next(reader, None)
                return sum(1 for _ in reader)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler {file_path}")


def classify_file(file_path: Path) -> str:
    """Classifica o arquivo por domínio de origem."""
    if file_path.name == "clientes.csv":
        return "clientes"
    if file_path.name.startswith("faturamento_export_"):
        return "faturamento"
    return "outros"


def brazil_timestamp() -> str:
    """Retorna o instante da ingestão no horário de São Paulo."""
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        except Exception:
            # Alguns ambientes Python não possuem o pacote de dados tzdata.
            pass

    brazil_offset = timezone(timedelta(hours=-3))
    return datetime.now(brazil_offset).isoformat()


def ingest_to_bronze(input_directory: Path, bronze_directory: Path) -> dict:
    """Copia os arquivos recebidos e cria o manifesto da execução."""
    run_id = uuid4().hex
    ingestion_timestamp = brazil_timestamp()
    files_metadata = []

    for source_path in sorted(input_directory.glob("*.csv")):
        domain = classify_file(source_path)
        destination_directory = bronze_directory / domain / run_id
        destination_directory.mkdir(parents=True, exist_ok=True)
        destination_path = destination_directory / source_path.name
        shutil.copy2(source_path, destination_path)

        files_metadata.append(
            {
                "source_file": source_path.name,
                "source_path": str(source_path),
                "bronze_path": str(destination_path),
                "domain": domain,
                "run_id": run_id,
                "ingestion_ts": ingestion_timestamp,
                "row_count": count_rows(source_path),
                "file_size_bytes": source_path.stat().st_size,
            }
        )

    if not files_metadata:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {input_directory}")

    manifest = {
        "run_id": run_id,
        "ingestion_ts": ingestion_timestamp,
        "files": files_metadata,
    }
    manifest_path = bronze_directory / "manifests" / f"{run_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    input_directory = project_root / "dados" / "entrada"
    bronze_directory = project_root / "dados" / "bronze"
    manifest = ingest_to_bronze(input_directory, bronze_directory)

    print(f"Bronze criada para run_id={manifest['run_id']}")
    for file_metadata in manifest["files"]:
        print(
            f"{file_metadata['source_file']}: "
            f"{file_metadata['row_count']} linhas -> "
            f"{file_metadata['bronze_path']}"
        )


if __name__ == "__main__":
    main()
