from .types import GraphResponse, PathResponse
from .utils import normalize_edge, normalize_node

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase, AsyncResult
from neo4j.exceptions import ServiceUnavailable


URI = "neo4j://localhost"
AUTH = ("neo4j", "neo4j")
DATABASE_NAME = "neo4j"

with open("app/queries/adjacent_artists.cypher", "r") as f:
    adjacent_artists_query = f.read()

with open("app/queries/search_artists.cypher", "r") as f:
    search_artists_query = f.read()

with open("app/queries/shortest_path.cypher", "r") as f:
    shortest_path_query = f.read()

@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = 60
    start_time = time.time()
    async with AsyncGraphDatabase.driver(URI, auth = AUTH) as driver:
        while True:
            try:
                await driver.verify_connectivity()
                break
            except (ServiceUnavailable, ConnectionResetError, OSError) as e:
                if time.time() - start_time > timeout:
                    print(f"Timeout of {timeout}s reached. Failed to connect to Neo4j.")
                    raise e

                print("Waiting for Neo4j initialization. Retrying in 5 seconds...")
                await asyncio.sleep(5)

        app.state.neo4j_driver = driver
        yield

app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In local testing phase, "*" can be used to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/artist/search")
async def search_artists(
    q: str,
    request: Request
):
    driver = request.app.state.neo4j_driver
    # Append ~ for fuzzy matching in Neo4j fulltext index
    query_param = f"{q}~"

    records, _, _ = await driver.execute_query(
        search_artists_query,
        query = query_param,
        database_ = DATABASE_NAME,
    )

    results = []
    for record in records:
        results.append({
            "id": record["id"],
            "name": record["name"],
            "disambiguation": record["disambiguation"],
            "score": record["finalScore"],
        })

    return results

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

@app.get("/artist/{source_artist_id}/shortest/{target_artist_id}")
async def get_shortest_path(
    source_artist_id: str,
    target_artist_id: str,
    request: Request
) -> PathResponse:
    if source_artist_id == target_artist_id:
        raise HTTPException(
            status_code=400,
            detail="Source and target must be different artists"
        )

    driver = request.app.state.neo4j_driver

    path_record = await driver.execute_query(
        shortest_path_query,
        idSource = source_artist_id,
        idTarget = target_artist_id,
        database_ = DATABASE_NAME,
        result_transformer_ = AsyncResult.single,
    )

    if path_record is None:
        raise HTTPException(
            status_code=404,
            detail="No path found between the artists within 10 hops"
        )

    nodes = []
    edges = []

    for artist in path_record["artists"]:
        nodes.append(normalize_node(artist))
    
    for rel_item in path_record["relationships"]:
        edge = normalize_edge(
            rel_item["relationship"],
            rel_item["start_id"],
            rel_item["end_id"]
        )
        edges.append(edge)

    path = [artist["id"] for artist in nodes]

    return {
        "source": source_artist_id,
        "target": target_artist_id,
        "path": path,
        "nodes": nodes,
        "edges": edges
    }

