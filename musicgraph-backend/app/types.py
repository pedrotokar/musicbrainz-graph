from typing import Any

from pydantic import BaseModel, Field

# --- MODELO DOS NÓS ---
class NodeModel(BaseModel):
    id: str
    labels: list[str] # ex: "Artist", "Band"
    display_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)

# --- MODELO DAS ARESTAS (RELAÇÕES) ---
class EdgeModel(BaseModel):
    source: str
    target: str
    type: str # ex: "COLLABORATED_WITH", "IS_CONTAINED_ON"

    parameters: dict[str, Any] = Field(default_factory=dict)

# --- RESPOSTA FINAL DA API ---
class GraphResponse(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]
