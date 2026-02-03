from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from langchain_core.messages import HumanMessage

from agent.graph import graph

app = FastAPI(title="AI Agent Service")


class AgentQueryRequest(BaseModel):
    """Request model for agent query."""

    query: str


class AgentQueryResponse(BaseModel):
    """Response model for agent query."""

    answer: Any


def _parse_content(content: Any) -> Any:
    """Parse JSON string content if possible."""

    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    return content


@app.post("/api/v1/agent/query", response_model=AgentQueryResponse)
async def query_agent(payload: AgentQueryRequest) -> AgentQueryResponse:
    """Invoke LangGraph agent with the provided query."""

    result = await graph.ainvoke({"messages": [HumanMessage(content=payload.query)]})
    last_message = result["messages"][-1]
    content = getattr(last_message, "content", last_message)
    return AgentQueryResponse(answer=_parse_content(content))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
