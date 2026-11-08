from typing import Any

from pydantic import BaseModel, Field

# --- NODE MODEL ---
class NodeModel(BaseModel):
    id: str
    labels: list[str] # ex: "Artist", "Band"
    display_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)

# --- EDGE MODEL (RELATIONSHIPS) ---
class EdgeModel(BaseModel):
    source: str
    target: str
    type: str # ex: "COLLABORATED_WITH", "IS_CONTAINED_ON"

    parameters: dict[str, Any] = Field(default_factory=dict)

# --- FINAL API RESPONSE ---
class GraphResponse(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]

# --- SHORTEST PATH RESPONSE ---
class PathResponse(GraphResponse):
    source: str
    target: str
    path: list[str]
