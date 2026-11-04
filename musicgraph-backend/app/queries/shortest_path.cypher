MATCH (a:Artist {id: $idSource})
MATCH p = shortestPath(
  (a)-[:INF_HAS_MUSICAL_CONNECTION_TO|INF_HAS_PERSONAL_CONNECTION_TO|INF_COLLABORATED_WITH|INF_COVERED|INF_PRODUCED*..10]-(b:Artist {id: $idTarget})
)
RETURN
  nodes(p) AS artists,
  relationships(p) AS relationships,
  length(p) AS distance
