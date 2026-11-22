// Encontrador de artistas originais de cada obra: (w:Work)-[:INF_ORIGINAL_ARTIST {recording_id}]->(oa:Artist)
//
// Regra:
//   1. Primeira gravação da obra (menor data de release; desempate por id).
//   2. Candidatos = escritores da obra (composer, writer, lyricist) + as bandas deles
//      (IS_RELATED_TO: member of band, founder, subgroup).
//   3. Originais = candidatos creditados nessa primeira gravação (união de banda e escritor).
//   4. Se nenhum candidato estiver creditado, a obra não recebe original (e não gera covers).
// recording_id guarda a primeira gravação, usada em 20_inf_covered.cypher.
//
// Limitações conhecidas (a inferência não captura):
//   - Música clássica e folk/tradicional (sem escritor gravado ou com [traditional] removido).
//   - Artistas proxy / shadow writers (escritor de aluguel que nunca gravou a obra).
//   - Datas de release ausentes ou parciais, que podem apontar a primeira gravação errada.
//   - Original fora do MusicBrainz, obras duplicadas e gravações sem Work vinculada.
//   - Lançamentos simultâneos (empate de data): o "original" fica arbitrário.
//   - Versões ao vivo, remix, remaster, medleys, traduções, samples e feats em versões posteriores.
//   - Aliases e renomeações de artista (artist rename / is person) não são unificados.
//   - "Various Artists" foi removido, então tributos e coletâneas creditados assim são perdidos.
MATCH (w:Work)
CALL (w) {
    // Primeira gravação da obra
    MATCH (w)<-[:IS_PERFORMANCE_OF]-(reco:Recording)-[:IS_CONTAINED_ON]->(rel:Release)
    WHERE rel.release_date IS NOT NULL
    WITH reco, MIN(rel.release_date) AS first_date
    ORDER BY first_date ASC, reco.id ASC
    LIMIT 1

    // Candidatos: escritores e as bandas deles
    MATCH (w)<-[p:PARTICIPATED_IN]-(writer:Artist)
    WHERE any(s IN p.subtypes WHERE s IN ["composer", "writer", "lyricist"])
    OPTIONAL MATCH (writer)-[m:IS_RELATED_TO]-(band:Artist)
    WHERE any(s IN m.subtypes WHERE s IN ["member of band", "founder", "subgroup"])
    WITH reco, COLLECT(DISTINCT writer) + COLLECT(DISTINCT band) AS candidates

    // União: candidatos creditados na primeira gravação
    UNWIND candidates AS c
    WITH DISTINCT reco, c
    WHERE (c)-[:CREDITED_IN]->(reco)
    MERGE (w)-[o:INF_ORIGINAL_ARTIST]->(c)
    SET o.recording_id = reco.id
} IN TRANSACTIONS OF 1000 ROWS
