from decimal import Decimal
from pathlib import Path

from src.business.gold import build_gold, margin


SILVER_PATH = Path(__file__).parents[1] / "dados" / "silver" / "faturamento.csv"


def test_margin_uses_aggregated_revenue_and_cost() -> None:
    assert margin(Decimal("100"), Decimal("60")) == Decimal("0.4")
    assert margin(Decimal("0"), Decimal("0")) is None


def test_gold_creates_consultant_and_detail_tables(tmp_path: Path) -> None:
    result = build_gold(SILVER_PATH, tmp_path)

    assert result["consultor_rows"] > 0
    assert result["detail_rows"] > result["consultor_rows"]
    assert (tmp_path / "comercial_margem_consultor.csv").exists()
    assert (tmp_path / "comercial_margem_detalhada.csv").exists()
