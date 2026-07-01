from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphResponse(BaseModel):
    scope: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
