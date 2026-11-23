// INF_SAMPLED: (artista que fez sample)-[:INF_SAMPLED {sampled_recordings, start_date}]->(artista sampleado)
MATCH (a:Artist)
CALL (a) {
    MATCH (a)-[cred:CREDITED_IN]->(r:Recording)
    MATCH (r)-[s:SAMPLES]->(r2:Recording|Release)<-[cred2:CREDITED_IN]-(b:Artist)
    WHERE a <> b
    OPTIONAL MATCH (r)-[:IS_CONTAINED_ON]->(rel:Release)
    WITH a, b,
         COLLECT(DISTINCT [[r.id, r.title, labels(r)], [r2.id, r2.title, labels(r2)]]) AS sampled_recordings,
         MIN(coalesce(r.performance_date, rel.release_date)) AS first_sampled_date
    MERGE (a)-[rel:INF_SAMPLED]->(b)
    SET rel.sampled_recordings = apoc.convert.toJson(sampled_recordings),
        rel.start_date = first_sampled_date
} IN TRANSACTIONS OF 1000 ROWS
