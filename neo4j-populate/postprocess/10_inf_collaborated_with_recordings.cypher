// INF_COLLABORATED_WITH a partir de gravações com créditos em comum.
// Bidirecional: guardada uma vez, do menor id para o maior (a.id < b.id).
// Deve rodar ANTES de 20_inf_from_is_related_to.cypher, para esta versão (com gravações) prevalecer.
// collaboration_recordings é gravado como JSON ([[id, title], ...]) pois o Neo4j não aceita listas aninhadas.
MATCH (a:Artist)
CALL (a) {
    MATCH (a)-[:CREDITED_IN]->(rec:Recording)<-[:CREDITED_IN]-(b:Artist)
    WHERE a.id < b.id
    MATCH (rec)-[:IS_CONTAINED_ON]->(rel:Release)
    WITH a, b, rec, MIN(rel.release_date) AS first_recording_release_date
    WITH a, b, COLLECT(DISTINCT [rec.id, rec.title]) AS collaboration_recordings, MIN(first_recording_release_date) AS first_collaboration_date
    MERGE (a)-[r:INF_COLLABORATED_WITH]->(b)
    SET r.collaboration_recordings = apoc.convert.toJson(collaboration_recordings),
        r.start_date = first_collaboration_date
} IN TRANSACTIONS OF 1000 ROWS
