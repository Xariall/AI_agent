from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastmcp.client import Client, PythonStdioTransport
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from agent.custom_tools import calculate_discount


MCP_SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp_server" / "server.py"
MCP_TRANSPORT = PythonStdioTransport(MCP_SERVER_PATH)
MCP_CLIENT = Client(MCP_TRANSPORT)


def _last_user_message(messages: list[BaseMessage]) -> str:
    """Return the latest human message content."""

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return ""


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text."""

    return [
        float(match.replace(",", "."))
        for match in re.findall(r"\d+(?:[.,]\d+)?", text)
    ]


def _tool_call(name: str, args: dict[str, Any]) -> AIMessage:
    """Create an AIMessage with a single tool call."""

    return AIMessage(
        content="",
        tool_calls=[
            {
                "id": "tool_call_1",
                "name": name,
                "args": args,
            }
        ],
    )


def _normalize_content(value: Any) -> Any:
    """Normalize tool output to plain dict/list when possible."""

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            root_match = re.search(
                r"Root\(id=(\d+), name='([^']*)', price=([0-9.]+), category='([^']*)', in_stock=(True|False)\)",
                value,
            )
            if root_match:
                return {
                    "id": int(root_match.group(1)),
                    "name": root_match.group(2),
                    "price": float(root_match.group(3)),
                    "category": root_match.group(4),
                    "in_stock": root_match.group(5) == "True",
                }
            return value
    if hasattr(value, "__root__"):
        return getattr(value, "__root__")
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict) and set(dumped.keys()) == {"root"}:
            return dumped["root"]
        return dumped
    if hasattr(value, "dict"):
        dumped = value.dict()
        if isinstance(dumped, dict) and set(dumped.keys()) == {"root"}:
            return dumped["root"]
        return dumped
    if hasattr(value, "root"):
        return value.root
    if isinstance(value, list):
        return [_normalize_content(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_content(val) for key, val in value.items()}
    return value


def _last_tool_call_name(messages: list[BaseMessage]) -> str | None:
    """Return the name of the latest tool call if present."""

    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.tool_calls:
            return message.tool_calls[0].get("name")
    return None


def _extract_category(text: str) -> str | None:
    """Extract category name from text."""

    match = re.search(r"категор\w*\s+([^\n,]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_product_id(text: str) -> int | None:
    """Extract product ID from text."""

    match = re.search(r"\bid\s*([0-9]+)", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_add_product_fields(text: str) -> dict[str, Any]:
    """Extract name, price, category fields for add_product."""

    name: str | None = None
    price: float | None = None
    category: str | None = None
    tail = text
    if ":" in text:
        tail = text.split(":", 1)[1]
    parts = [part.strip() for part in tail.split(",") if part.strip()]
    for part in parts:
        lowered = part.lower()
        if "цен" in lowered:
            numbers = _extract_numbers(part)
            if numbers:
                price = numbers[0]
        elif "категор" in lowered:
            category = part.split(" ", 1)[1].strip() if " " in part else None
        elif name is None:
            name = part
    return {
        "name": name or "Новый товар",
        "price": float(price) if price is not None else 0.0,
        "category": category or "Без категории",
    }


async def _call_mcp_tool(name: str, args: dict[str, Any]) -> Any:
    """Call MCP tool via stdio subprocess and return its data."""

    async with MCP_CLIENT:
        result = await MCP_CLIENT.call_tool(name, args)
    if result.data is not None:
        return _normalize_content(result.data)
    if result.structured_content is not None:
        return _normalize_content(result.structured_content)
    return _normalize_content(result.content)


@tool("list_products")
async def list_products_tool() -> list[dict[str, Any]]:
    """List all products from MCP server."""

    payload = await _call_mcp_tool("list_products", {})
    return payload


@tool("get_product")
async def get_product_tool(product_id: int) -> dict[str, Any]:
    """Get a product by id from MCP server."""

    payload = await _call_mcp_tool("get_product", {"product_id": product_id})
    return payload


@tool("add_product")
async def add_product_tool(
    name: str,
    price: float,
    category: str,
    in_stock: bool = True,
) -> dict[str, Any]:
    """Add a product via MCP server."""

    payload = await _call_mcp_tool(
        "add_product",
        {
            "name": name,
            "price": price,
            "category": category,
            "in_stock": in_stock,
        },
    )
    return payload


@tool("get_statistics")
async def get_statistics_tool() -> dict[str, Any]:
    """Get product statistics from MCP server."""

    payload = await _call_mcp_tool("get_statistics", {})
    return payload


def mock_llm(state: MessagesState) -> dict[str, list[BaseMessage]]:
    """Mock LLM that routes to tools using keyword heuristics."""

    messages = state["messages"]
    if messages and isinstance(messages[-1], ToolMessage):
        tool_name = _last_tool_call_name(messages) or ""
        last_user = _last_user_message(messages).lower()
        content = _normalize_content(messages[-1].content)
        if tool_name == "list_products" and "категор" in last_user:
            category = _extract_category(last_user)
            if isinstance(content, list) and category:
                filtered = [
                    item
                    for item in content
                    if str(item.get("category", "")).lower()
                    == category.lower()
                ]
                return {
                    "messages": [
                        AIMessage(
                            content=json.dumps(
                                filtered, ensure_ascii=False, indent=2
                            )
                        )
                    ]
                }
        if tool_name == "get_product" and "скидк" in last_user:
            numbers = _extract_numbers(last_user)
            percentage = numbers[0] if numbers else 10.0
            if isinstance(content, dict) and "price" in content:
                return {
                    "messages": [
                        _tool_call(
                            "calculate_discount",
                            {
                                "price": float(content["price"]),
                                "percentage": percentage,
                            },
                        )
                    ]
                }
        if isinstance(content, (dict, list)):
            return {
                "messages": [
                    AIMessage(
                        content=json.dumps(content, ensure_ascii=False, indent=2)
                    )
                ]
            }
        return {"messages": [AIMessage(content=str(content))]}

    raw_text = _last_user_message(state["messages"])
    text = raw_text.lower()
    if "добав" in text:
        fields = _extract_add_product_fields(raw_text)
        price = fields["price"]
        in_stock = not any(
            marker in text
            for marker in ("не в наличии", "нет в наличии", "out of stock")
        )
        return {
            "messages": [
                _tool_call(
                    "add_product",
                    {
                        "name": fields["name"],
                        "price": price,
                        "category": fields["category"],
                        "in_stock": in_stock,
                    },
                )
            ]
        }
    if "электрон" in text or "категор" in text:
        return {"messages": [_tool_call("list_products", {})]}
    if "цен" in text or "статист" in text:
        return {"messages": [_tool_call("get_statistics", {})]}
    if "скидк" in text:
        product_id = _extract_product_id(raw_text)
        if product_id is not None:
            return {
                "messages": [_tool_call("get_product", {"product_id": product_id})]
            }
        numbers = _extract_numbers(text)
        price = 100.0
        percentage = 10.0
        if len(numbers) >= 2:
            first, second = numbers[0], numbers[1]
            if first <= 100:
                percentage, price = first, second
            else:
                price, percentage = first, second
        elif len(numbers) == 1:
            price = numbers[0]
        return {
            "messages": [
                _tool_call(
                    "calculate_discount",
                    {"price": price, "percentage": percentage},
                )
            ]
        }
    return {"messages": [AIMessage(content="Запрос не распознан.")]}


def build_graph() -> Any:
    """Build and compile the LangGraph state machine."""

    tools = [
        list_products_tool,
        get_product_tool,
        add_product_tool,
        get_statistics_tool,
        calculate_discount,
    ]

    builder = StateGraph(MessagesState)
    builder.add_node("agent", mock_llm)
    builder.add_node("tools", ToolNode(tools))
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    builder.set_entry_point("agent")
    return builder.compile()


graph = build_graph()
