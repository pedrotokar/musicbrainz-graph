from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase, AsyncResult
from neo4j.graph import Node, Relationship


# from pydantic import BaseModel, Field
# from typing import Dict, Any, List

# # --- MODELO DOS NÓS ---
# class NodeModel(BaseModel):
#     id: str
#     label: str # ex: "Artist", "Band"
#     name: str
#     # O "pulo do gato": um dicionário que aceita qualquer coisa!
#     properties: Dict[str, Any] = Field(default_factory=dict)

# # --- MODELO DAS ARESTAS (RELAÇÕES) ---
# class EdgeModel(BaseModel):
#     source: str
#     target: str
#     type: str # ex: "COLLABORATED_WITH", "INFLUENCED"
    
#     # Tudo que for específico daquela relação cai aqui dentro
#     properties: Dict[str, Any] = Field(default_factory=dict)

# # --- RESPOSTA FINAL DA API ---
# class GraphResponse(BaseModel):
#     nodes: List[NodeModel]
#     edges: List[EdgeModel]


URI = "neo4j://localhost"
AUTH = ("neo4j", "neo4j")
DATABASE_NAME = "neo4j"

def normalize_node(node: Node):
    node_dict = {}

    node_dict["id"] = node.get("id")
    node_dict["display_name"] = node.get("name") or node.get("title")
    node_dict["labels"] = list(node.labels)

    node_dict["parameters"] = {}
    for key, value in node.items():
        if key == "id": continue
        node_dict["parameters"][key] = value

    return node_dict

def normalize_edge(edge: Relationship, start_id: str, end_id: str):
    edge_dict = {}

    # edge_dict["source"] = edge.start_node.get("id")
    # edge_dict["target"] = edge.end_node.get("id") # unfortunatly that doesn't work well
    edge_dict["source"] = start_id
    edge_dict["target"] = end_id
    edge_dict["type"] = edge.type

    edge_dict["parameters"] = {}
    for key, value in edge.items():
        edge_dict["parameters"][key] = value
    
    return edge_dict

# async with request.app.state.neo4j_driver.session(database = DATABASE_NAME) as session:
#     artist_adjacents = await session.execute_read(
#         retrieve_artist_adjacents,
#         artist_id
#     )
#     return artist_adjacents

# async def retrieve_artist_adjacents(tx, artist_id):
#     result = await tx.run("""
#     MATCH (artist:Artist {id: $id})-[relation]-(artist2:Artist) RETURN artist, relation, artist2
#     """, id = artist_id)
#     records = []
#     async for record in result:
#         print(record)
#         print(type(record))
#     return records



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncGraphDatabase.driver(URI, auth = AUTH) as driver:
        await driver.verify_connectivity()
        app.state.neo4j_driver = driver
        yield

app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na fase de testes locais, pode usar "*" para liberar tudo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/artist/{artist_id}/adjacent")
async def get_near_artists(
    artist_id: str,
    request: Request
):

    nodes = []
    edges = []
    node_ids = set()
    
    driver = request.app.state.neo4j_driver

    main_artist_record = await driver.execute_query("""
        MATCH (artist:Artist {id: $id}) RETURN artist;
        """, 
        id = artist_id,
        database_ = DATABASE_NAME,
        result_transformer_ = AsyncResult.single,
    )

    main_artist_node = normalize_node(main_artist_record["artist"])
    nodes.append(main_artist_node)
    node_ids.add(main_artist_node["id"])

    records, _, _ = await driver.execute_query("""
        MATCH (:Artist {id: $id})-[relationship]-(artist:Artist) 
        RETURN 
            relationship, 
            artist,
            startNode(relationship).id AS start_id,
            endNode(relationship).id AS end_id;
        """, 
        id = artist_id,
        database_ = DATABASE_NAME,
    )

    for record in records:
        other_artist_node = normalize_node(record["artist"])
        if not (other_artist_node["id"] in node_ids):
            nodes.append(other_artist_node)
            node_ids.add(other_artist_node["id"])

        edges.append(
            normalize_edge(
                record["relationship"],
                record["start_id"],
                record["end_id"]
            )
        )
        #break

    return {
        "nodes": nodes,
        "edges": edges
    }

