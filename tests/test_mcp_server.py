from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server import server


@pytest.fixture()
def storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patch storage paths to a temporary directory."""

    data_dir = tmp_path / "data"
    products_path = data_dir / "products.json"
    monkeypatch.setattr(server, "DATA_DIR", data_dir)
    monkeypatch.setattr(server, "PRODUCTS_PATH", products_path)
    return products_path


def test_list_products_empty(storage: Path) -> None:
    """list_products returns empty list for empty storage."""

    assert server.list_products_data() == []


def test_add_and_get_product(storage: Path) -> None:
    """add_product stores entry and get_product fetches it."""

    added = server.add_product_data(
        name="Notebook",
        price=4.5,
        category="Stationery",
        in_stock=True,
    )
    fetched = server.get_product_data(added["id"])
    assert fetched == added


def test_get_product_not_found(storage: Path) -> None:
    """get_product raises ValueError when not found."""

    with pytest.raises(ValueError):
        server.get_product_data(999)


def test_statistics(storage: Path) -> None:
    """get_statistics returns total and average price."""

    server.add_product_data("A", 10.0, "Test", True)
    server.add_product_data("B", 20.0, "Test", False)
    stats = server.get_statistics_data()
    assert stats["total_count"] == 2
    assert stats["average_price"] == 15.0


def test_storage_format(storage: Path) -> None:
    """Storage file is valid JSON list."""

    server.add_product_data("Pen", 1.2, "Stationery", True)
    raw = storage.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, list)
