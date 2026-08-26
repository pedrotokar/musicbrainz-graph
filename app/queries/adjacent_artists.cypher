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

    //Derived from default connections
    MATCH (sourceArtist:Artist {id: id})
    MATCH (sourceArtist)-[relationship:IS_RELATED_TO]-(artist:Artist)
    WITH sourceArtist, relationship, artist, 
        CASE
            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["member of band", "subgroup", "artist rename", "artistic director", "conductor position", "founder", "supporting musician", "vocal supporting musician", "instrumental supporting musician", "tribute", "voice actor", "is person", "teacher", "artist-in-residence", "composer-in-residence"])
            THEN {type: "HAS_MUSICAL_CONNECTION_TO", attributes: {subtypes: relationship.subtypes}}

            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["parent", "sibling", "married", "involved with", "named after artist"])
            THEN {type: "HAS_PERSONAL_CONNECTION_TO", attributes: {subtypes: relationship.subtypes}}

            WHEN any(subtype IN relationship.subtypes WHERE subtype in ["collaboration"])
            THEN {type: "COLLABORATED_WITH", attributes: {collaboration_recordings: NULL}}
        END as vRelationshipData
    WHERE vRelationshipData IS NOT NULL
    CALL apoc.create.vRelationship(startNode(relationship), vRelationshipData.type, vRelationshipData.attributes, endNode(relationship)) YIELD rel AS vRelationship
    RETURN sourceArtist, vRelationship, artist

    UNION ALL

    //Collaborations
    MATCH (sourceArtist:Artist {id: id})
    MATCH (sourceArtist)-[cred:CREDITED_IN]->(rec:Recording)<-[cred2:CREDITED_IN]-(artist:Artist)
    MATCH (rec)-[cont:IS_CONTAINED_ON]->(rel:Release)
    WITH sourceArtist, COLLECT([rec.id, rec.title]) AS collaboration_recordings, MIN(rel.release_date) AS first_collaboration_date, artist
    CALL apoc.create.vRelationship(sourceArtist,'COLLABORATED_WITH', {collaboration_recordings: collaboration_recordings, start_date: first_collaboration_date}, artist) YIELD rel AS vRelationship
    RETURN sourceArtist, vRelationship, artist

    UNION ALL

    //Production 
    MATCH (sourceArtist:Artist {id: id}) 
    MATCH (sourceArtist)-[rel1:PARTICIPATED_IN|CREDITED_IN]->(r:Release|Recording)<-[rel2:CREDITED_IN|PARTICIPATED_IN]-(artist:Artist)
    WHERE 
        (type(rel1) = "PARTICIPATED_IN" AND "producer" IN rel1.subtypes AND type(rel2) = "CREDITED_IN") OR
        (type(rel2) = "PARTICIPATED_IN" AND "producer" IN rel2.subtypes AND type(rel1) = "CREDITED_IN")
    WITH sourceArtist, artist, r,
        CASE WHEN type(rel1) = "PARTICIPATED_IN" THEN sourceArtist ELSE artist END AS vSource,
        CASE WHEN type(rel1) = "PARTICIPATED_IN" THEN artist ELSE sourceArtist END AS vTarget
    WITH sourceArtist, artist, vSource, vTarget, COLLECT([r.id, r.title, labels(r)]) AS produced_recordings
    CALL apoc.create.vRelationship(vSource, "PRODUCED", {produced_recordings: produced_recordings}, vTarget) YIELD rel as vRelationship
    RETURN sourceArtist, vRelationship, artist

}
RETURN
    vRelationship as relationship,
    artist,
    startNode(vRelationship).id AS start_id,
    endNode(vRelationship).id AS end_id;
