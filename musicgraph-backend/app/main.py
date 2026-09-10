from .types import GraphResponse
from .utils import normalize_edge, normalize_node

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase, AsyncResult


URI = "neo4j://localhost"
AUTH = ("neo4j", "neo4j")
DATABASE_NAME = "neo4j"

with open("app/queries/adjacent_artists.cypher", "r") as f:
    adjacent_artists_query = f.read()


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
) -> GraphResponse:

    nodes = []
    edges = []
    node_ids = set()
    
    driver = request.app.state.neo4j_driver

    main_artist_record = await driver.execute_query(
        "MATCH (artist:Artist {id: $id}) RETURN artist;", 
        id = artist_id,
        database_ = DATABASE_NAME,
        result_transformer_ = AsyncResult.single,
    )

    main_artist_node = normalize_node(main_artist_record["artist"])
    nodes.append(main_artist_node)
    node_ids.add(main_artist_node["id"])

    records, _, _ = await driver.execute_query(
        adjacent_artists_query, 
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

    return {
        "nodes": nodes,
        "edges": edges
    }

