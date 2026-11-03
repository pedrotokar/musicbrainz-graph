// INF_HAS_MUSICAL_CONNECTION_TO, INF_HAS_PERSONAL_CONNECTION_TO, INF_COLLABORATED_WITH e INF_COVERED
// derivadas das relações IS_RELATED_TO. A prioridade do CASE é a mesma da query original.
// Tipos bidirecionais (HAS_*, COLLABORATED_WITH): guardados do menor id para o maior, com subtypes unidos.
// COVERED é direcionada e mantém a direção original.
// Para COLLABORATED_WITH, as propriedades só entram na criação: se já existir a aresta de
// 10_inf_collaborated_with_recordings.cypher, ela prevalece e não é alterada.
MATCH (x:Artist)-[rel:IS_RELATED_TO]->(y:Artist)
WHERE x <> y
WITH x, y, rel,
    CASE
        WHEN any(subtype IN rel.subtypes WHERE subtype IN ["member of band", "subgroup", "artist rename", "artistic director", "conductor position", "founder", "supporting musician", "vocal supporting musician", "instrumental supporting musician", "voice actor", "is person", "teacher", "artist-in-residence", "composer-in-residence"])
        THEN {type: "INF_HAS_MUSICAL_CONNECTION_TO", bidirectional: TRUE}

        WHEN any(subtype IN rel.subtypes WHERE subtype IN ["parent", "sibling", "married", "involved with", "named after artist"])
        THEN {type: "INF_HAS_PERSONAL_CONNECTION_TO", bidirectional: TRUE}

        WHEN any(subtype IN rel.subtypes WHERE subtype IN ["collaboration"])
        THEN {type: "INF_COLLABORATED_WITH", bidirectional: TRUE}

        WHEN any(subtype IN rel.subtypes WHERE subtype IN ["tribute"])
        THEN {type: "INF_COVERED", bidirectional: FALSE}
    END AS data
WHERE data IS NOT NULL
WITH
    CASE WHEN data.bidirectional AND x.id > y.id THEN y ELSE x END AS src,
    CASE WHEN data.bidirectional AND x.id > y.id THEN x ELSE y END AS dst,
    data.type AS type,
    rel.subtypes AS subtypes
WITH src, dst, type, apoc.coll.toSet(apoc.coll.flatten(COLLECT(subtypes))) AS subtypes
WITH src, dst, type,
    CASE type
        WHEN "INF_HAS_MUSICAL_CONNECTION_TO" THEN {subtypes: subtypes}
        WHEN "INF_HAS_PERSONAL_CONNECTION_TO" THEN {subtypes: subtypes}
        WHEN "INF_COVERED" THEN {is_tribute_band: TRUE}
        ELSE {}
    END AS props
CALL (src, dst, type, props) {
    // Como são várias relações diferentes, preciso usar essa chamada no lugar
    // da instrução MERGE
    CALL apoc.merge.relationship(src, type, {}, props, dst, {}) YIELD rel
    RETURN count(rel) AS created
} IN TRANSACTIONS OF 10000 ROWS
RETURN count(*) AS processed
