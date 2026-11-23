// INF_PRODUCED: (produtor)-[:INF_PRODUCED {produced_recordings, start_date}]->(artista creditado na mesma release/recording).
// Direcionada. Partindo sempre do produtor, cada par é gerado uma única vez.
// produced_recordings é gravado como JSON ([[id, title, labels], ...]).
MATCH (a:Artist)
CALL (a) {
    MATCH (a)-[p:PARTICIPATED_IN]->(r:Release|Recording)<-[:CREDITED_IN]-(b:Artist)
    WHERE "producer" IN p.subtypes AND a <> b
    OPTIONAL MATCH (r)-[:IS_CONTAINED_ON]->(rel:Release)
    WITH a, b, r,
         CASE
             WHEN "Release" IN labels(r) THEN r.release_date
             ELSE coalesce(r.performance_date, rel.release_date)
         END AS prod_date
    WITH a, b,
         COLLECT(DISTINCT [r.id, r.title, labels(r)]) AS produced_recordings,
         MIN(prod_date) AS first_production_date
    MERGE (a)-[rel:INF_PRODUCED]->(b)
    SET rel.produced_recordings = apoc.convert.toJson(produced_recordings),
        rel.start_date = first_production_date
} IN TRANSACTIONS OF 1000 ROWS
