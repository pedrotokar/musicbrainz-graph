// MATCH (sourceArtist:Artist {id: $id})
// MATCH (sourceArtist)-[relationship]-(artist:Artist) 
// RETURN 
//     relationship, 
//     artist,
//     startNode(relationship).id AS start_id,
//     endNode(relationship).id AS end_id;

// "member of band",
// "subgroup",
// "artist rename",
// "artistic director",
// "conductor position",
// "founder",
// "supporting musician",
// "vocal supporting musician",
// "instrumental supporting musician",
// "tribute",
// "voice actor",
// "collaboration",
// "is person",
// "teacher",
// "artist-in-residence",
// "composer-in-residence",

// "parent",
// "sibling",
// "married",
// "involved with",
// "named after artist",

WITH $id AS id
CALL (id) {
    MATCH (sourceArtist:Artist {id: id})
    MATCH (sourceArtist)-[relationship:IS_RELATED_TO]-(artist:Artist)
    WITH sourceArtist, relationship, artist, 
        CASE
            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["member of band", "subgroup", "artist rename", "artistic director", "conductor position", "founder", "supporting musician", "vocal supporting musician", "instrumental supporting musician", "tribute", "voice actor", "is person", "teacher", "artist-in-residence", "composer-in-residence"])
            THEN {type: "HAS_MUSICAL_CONNECTION_TO", attributes: {subtypes: relationship.subtypes}}

            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["parent", "sibling", "married", "involved with", "named after artist"])
            THEN {type: "HAS_PERSONAL_CONNECTION_TO", attributes: {subtypes: relationship.subtypes}}

            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["collaboration"])
            THEN {type: "HAS_COLLABORATED_WITH", attributes: {collaboration_recordings: NULL}}
        END as vRelationshipData
    WHERE vRelationshipData IS NOT NULL
    CALL apoc.create.vRelationship(startNode(relationship), vRelationshipData.type, vRelationshipData.attributes, endNode(relationship)) YIELD rel AS vRelationship
    RETURN sourceArtist, vRelationship, artist
    UNION ALL
    MATCH (sourceArtist:Artist {id: id})
    MATCH (sourceArtist)-[cred:CREDITED_IN]->(rec:Recording)<-[cred2:CREDITED_IN]-(artist:Artist)
    MATCH (rec)-[cont:IS_CONTAINED_ON]->(rel:Release)
    WITH sourceArtist, COLLECT([rec.id, rec.title]) AS collaboration_recordings, MIN(rel.release_date) AS first_collaboration_date, artist
    CALL apoc.create.vRelationship(sourceArtist,'HAS_COLLABORATED_WITH', {collaboration_recordings: collaboration_recordings, start_date: first_collaboration_date}, artist) YIELD rel AS vRelationship
    RETURN sourceArtist, vRelationship, artist
}
RETURN
    vRelationship as relationship,
    artist,
    startNode(vRelationship).id AS start_id,
    endNode(vRelationship).id AS end_id;
