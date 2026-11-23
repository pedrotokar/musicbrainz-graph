// INF_COVERED: (artista que fez cover)-[:INF_COVERED {covered_songs, start_date}]->(artista original)
// Direcionada: o source é quem fez o cover, o target é o original (mesma convenção da aresta de tribute).
// Usa os originais de 15_inf_original_artist.cypher (que deve rodar antes).
// Deve rodar ANTES de 30_inf_from_is_related_to.cypher, para esta versão (com as músicas) prevalecer
// sobre o INF_COVERED derivado de "tribute".
// covered_songs é gravado como JSON ([[work_id, title], ...]) pois o Neo4j não aceita listas aninhadas.
// Veja as limitações da heurística em 15_inf_original_artist.cypher.
MATCH (ca:Artist)
CALL (ca) {
    MATCH (ca)-[:CREDITED_IN]->(rec:Recording)-[perf:IS_PERFORMANCE_OF]->(w:Work)-[o:INF_ORIGINAL_ARTIST]->(oa:Artist)
    // Ignora a própria primeira gravação e quem é original da mesma obra
    WHERE rec.id <> o.recording_id
      AND NOT (w)-[:INF_ORIGINAL_ARTIST]->(ca)
    OPTIONAL MATCH (rec)-[:IS_CONTAINED_ON]->(rel:Release)
    WITH ca, oa, w,
         coalesce(perf.start_date, rel.release_date) AS track_date
    WITH ca, oa,
         COLLECT(DISTINCT [w.id, w.title]) AS covered_songs,
         MIN(track_date) AS first_covered_date
    MERGE (ca)-[r:INF_COVERED]->(oa)
    SET r.covered_songs = apoc.convert.toJson(covered_songs),
        r.start_date = first_covered_date
} IN TRANSACTIONS OF 1000 ROWS
