// INF_PRODUCED: (produtor)-[:INF_PRODUCED]->(artista creditado na mesma release/recording).
// Direcionada. Partindo sempre do produtor, cada par é gerado uma única vez.
// produced_recordings é gravado como JSON ([[id, title, labels], ...]).
MATCH (a:Artist)
CALL (a) {
    MATCH (a)-[p:PARTICIPATED_IN]->(r:Release|Recording)<-[:CREDITED_IN]-(b:Artist)
    WHERE "producer" IN p.subtypes AND a <> b
    WITH a, b, COLLECT(DISTINCT [r.id, r.title, labels(r)]) AS produced_recordings
    MERGE (a)-[rel:INF_PRODUCED]->(b)
    SET rel.produced_recordings = apoc.convert.toJson(produced_recordings)
} IN TRANSACTIONS OF 1000 ROWS
