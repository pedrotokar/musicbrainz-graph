MATCH (a:Artist)
CALL (a) {
    MATCH (a)-[cred:CREDITED_IN]->(r:Recording)
    MATCH (r)-[s:SAMPLES]->(r2:Recording|Release)<-[cred2:CREDITED_IN]-(b:Artist)
    WHERE a <> b
    WITH a, b, COLLECT(DISTINCT [[r.id, r.title, labels(r)], [r2.id, r2.title, labels(r2)]]) AS sampled_recordings
    MERGE (a)-[rel:INF_SAMPLED]->(b)
    SET rel.sampled_recordings = apoc.convert.toJson(sampled_recordings)
} IN TRANSACTIONS OF 1000 ROWS
