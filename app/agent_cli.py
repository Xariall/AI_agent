from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from langchain_core.messages import HumanMessage

from agent.graph import graph


def _print_json(payload: Any) -> None:
    """Print JSON payload to stdout."""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Agent CLI")
    parser.add_argument("query", type=str, help="User query for the agent")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    args = build_parser().parse_args(argv)
    result = asyncio.run(
        graph.ainvoke({"messages": [HumanMessage(content=args.query)]})
    )
    last_message = result["messages"][-1]
    content = getattr(last_message, "content", last_message)
    if isinstance(content, (dict, list)):
        _print_json(content)
    else:
        print(str(content))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
