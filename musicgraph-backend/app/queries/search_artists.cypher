CALL db.index.fulltext.queryNodes("artist_search", $query) YIELD node, score
MATCH (node)-[r]-()
WITH node, score, count(r) AS degree
// Cria um score final que mistura a semelhança do texto com a popularidade do nó
RETURN node.id AS id, node.name AS name, (score * (1 + log10(degree + 1))) AS finalScore
ORDER BY finalScore DESC
LIMIT 10;
