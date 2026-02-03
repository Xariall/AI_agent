from __future__ import annotations

import json
from pathlib import Path
from typing_extensions import TypedDict

from fastmcp import FastMCP


class Product(TypedDict):
    """Represents a product entry stored in products.json."""

    id: int
    name: str
    price: float
    category: str
    in_stock: bool


mcp = FastMCP("ai-agent-test")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PRODUCTS_PATH = DATA_DIR / "products.json"


def _ensure_storage() -> None:
    """Ensure the products storage file exists."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PRODUCTS_PATH.exists():
        PRODUCTS_PATH.write_text("[]", encoding="utf-8")


def _load_products() -> list[Product]:
    """Load products from the local JSON file."""

    _ensure_storage()
    raw = PRODUCTS_PATH.read_text(encoding="utf-8")
    data = json.loads(raw) if raw.strip() else []
    return data


def _save_products(products: list[Product]) -> None:
    """Persist products to the local JSON file."""

    _ensure_storage()
    PRODUCTS_PATH.write_text(
        json.dumps(products, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_products_data() -> list[Product]:
    """Return the full list of products."""

    return _load_products()


def get_product_data(product_id: int) -> Product:
    """Return a single product by id or raise ValueError."""

    products = _load_products()
    for product in products:
        if product["id"] == product_id:
            return product
    raise ValueError(f"Product with id={product_id} not found.")


def add_product_data(
    name: str,
    price: float,
    category: str,
    in_stock: bool,
) -> Product:
    """Add a new product to storage and return it."""

    products = _load_products()
    next_id = max((product["id"] for product in products), default=0) + 1
    new_product: Product = {
        "id": next_id,
        "name": name,
        "price": float(price),
        "category": category,
        "in_stock": bool(in_stock),
    }
    products.append(new_product)
    _save_products(products)
    return new_product


def get_statistics_data() -> dict[str, float | int]:
    """Return total product count and average price."""

    products = _load_products()
    total_count = len(products)
    average_price = (
        sum(product["price"] for product in products) / total_count
        if total_count > 0
        else 0.0
    )
    return {"total_count": total_count, "average_price": average_price}


@mcp.tool
def list_products() -> list[Product]:
    """Return the full list of products."""

    return list_products_data()


@mcp.tool
def get_product(product_id: int) -> Product:
    """Return a single product by id or raise ValueError."""

    return get_product_data(product_id)


@mcp.tool
def add_product(name: str, price: float, category: str, in_stock: bool) -> Product:
    """Add a new product to storage and return it."""

    return add_product_data(name, price, category, in_stock)


@mcp.tool
def get_statistics() -> dict[str, float | int]:
    """Return total product count and average price."""

    return get_statistics_data()


if __name__ == "__main__":
    mcp.run()
