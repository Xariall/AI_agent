from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server import server


def _print_json(payload: Any) -> None:
    """Print JSON payload to stdout."""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _handle_list(_: argparse.Namespace) -> int:
    """Handle list command."""

    _print_json(server.list_products_data())
    return 0


def _handle_get(args: argparse.Namespace) -> int:
    """Handle get command."""

    try:
        product = server.get_product_data(args.product_id)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _print_json(product)
    return 0


def _handle_add(args: argparse.Namespace) -> int:
    """Handle add command."""

    in_stock = not args.out_of_stock
    product = server.add_product_data(
        name=args.name,
        price=args.price,
        category=args.category,
        in_stock=in_stock,
    )
    _print_json(product)
    return 0


def _handle_stats(_: argparse.Namespace) -> int:
    """Handle stats command."""

    _print_json(server.get_statistics_data())
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Products CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List all products")
    list_parser.set_defaults(handler=_handle_list)

    get_parser = subparsers.add_parser("get", help="Get product by id")
    get_parser.add_argument("product_id", type=int, help="Product id")
    get_parser.set_defaults(handler=_handle_get)

    add_parser = subparsers.add_parser("add", help="Add new product")
    add_parser.add_argument("name", type=str, help="Product name")
    add_parser.add_argument("price", type=float, help="Product price")
    add_parser.add_argument("category", type=str, help="Product category")
    add_parser.add_argument(
        "--out-of-stock",
        action="store_true",
        help="Mark product as out of stock",
    )
    add_parser.set_defaults(handler=_handle_add)

    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(handler=_handle_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
