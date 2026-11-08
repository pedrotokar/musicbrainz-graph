MATCH (a:Artist {id: $idSource}), (b:Artist {id: $idTarget})
MATCH p = ANY SHORTEST (a) ( ()-[:INF_HAS_MUSICAL_CONNECTION_TO|INF_HAS_PERSONAL_CONNECTION_TO|INF_COLLABORATED_WITH|INF_COVERED|INF_PRODUCED]-() ){1, 10} (b)
RETURN
  nodes(p) AS artists,
  [r IN relationships(p) | {relationship: r, start_id: startNode(r).id, end_id: endNode(r).id}] AS relationships,
  length(p) AS distance
