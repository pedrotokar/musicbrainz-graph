MATCH (:Artist {id: $id})-[relationship]-(artist:Artist) 
RETURN 
    relationship, 
    artist,
    startNode(relationship).id AS start_id,
    endNode(relationship).id AS end_id;
