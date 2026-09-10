from neo4j.graph import Node, Relationship
from .types import EdgeModel, NodeModel

def normalize_node(node: Node) -> NodeModel:
    node_dict = {}

    node_dict["id"] = node.get("id")
    node_dict["display_name"] = node.get("name") or node.get("title")
    node_dict["labels"] = list(node.labels)

    node_dict["parameters"] = {}
    for key, value in node.items():
        if key == "id": continue
        node_dict["parameters"][key] = value

    return node_dict

def normalize_edge(edge: Relationship, start_id: str, end_id: str) -> EdgeModel:
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
