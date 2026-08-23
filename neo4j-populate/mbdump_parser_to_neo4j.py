from collections import defaultdict
from datetime import datetime
import json
from os.path import isfile
import subprocess
import sys
import tarfile

from neo4j import GraphDatabase
from tqdm import tqdm

def datetime_valid(dt_str):
    if not dt_str or not isinstance(dt_str, str):
        return False
        
    parts = dt_str.split("-")
    
    if len(parts) == 1:
        dt_str_to_check = dt_str + "-01-01"
    elif len(parts) == 2:
        dt_str_to_check = dt_str + "-01"
    else:
        dt_str_to_check = dt_str
        
    try:
        datetime.fromisoformat(dt_str_to_check)
        return True
    except ValueError:
        return False

# ==========================================
# 1. CONFIGURAÇÃO DO NEO4J
# ==========================================

URI = "neo4j://localhost"
AUTH = ("neo4j", "neo4j")
BATCH_SIZE = 10000

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

driver.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Artist) REQUIRE n.id IS UNIQUE")
driver.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Work) REQUIRE n.id IS UNIQUE")
driver.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Release) REQUIRE n.id IS UNIQUE")
driver.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:ReleaseGroup) REQUIRE n.id IS UNIQUE")
driver.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Recording) REQUIRE n.id IS UNIQUE")

def get_batch_insert_function(query):
    def batch_insert(tx, batch):
        tx.run(query, batch = batch)
    return batch_insert

# ==========================================
# 2. DEFINIÇÃO DE QUERIES
# ==========================================

entities = [
    "artist",
    "recording",
    "release",
    "releasegroup",
    "work",
]

entity_queries = {
    "artist": """
        UNWIND $batch AS data
        MERGE (n:Artist {id: data.id})
        SET n.name = coalesce(data.name, n.name), 
            n.begin = coalesce(data.begin, n.begin), 
            n.end = coalesce(data.end, n.end), 
            n.ended = coalesce(data.ended, n.ended), 
            n.type = coalesce(data.type, n.type)
    """, 
    "recording": """
        UNWIND $batch AS data
        MERGE (n:Recording {id: data.id})
        SET n.title = coalesce(data.title, n.title)
    """,
    "release": """
        UNWIND $batch AS data
        MERGE (n:Release {id: data.id})
        SET n.title = coalesce(data.title, n.title), 
            n.release_date = coalesce(date(data.date), n.release_date), 
            n.status = coalesce(data.status, n.status)
    """,
    "releasegroup": """
        UNWIND $batch AS data
        MERGE (n:ReleaseGroup {id: data.id})
        SET n.title = coalesce(data.title, n.title),
            n.type = coalesce(data["primary-type"], n.type),
            n.secondary_types = coalesce(data["secondary-types"], n.secondary_types),
            n.first_release_date = coalesce(date(data["first-release-date"]), n.first_release_date)
    """,
    "work": """
        UNWIND $batch AS data
        MERGE (n:Work {id: data.id})
        SET n.title = coalesce(data.title, n.title), 
            n.type = coalesce(data.type, n.type)
    """, 
}

relationships = [
    "recording_work_performance", # ESSA TALVEZ VIRE GENÉRICA. NO FIM É SÓ UM SUBTIPO
    "recording_release_contained", # ÓBVIA
    "recording_release_sample",# ESSA TALVEZ VIRE GENÉRICA. NO FIM É SÓ UM SUBTIPO
    "recording_recording_sample",# ESSA TALVEZ VIRE GENÉRICA. NO FIM É SÓ UM SUBTIPO
    "release_releasegroup_instance", # ÓBVIA
    "artist_artist_generic",
    "artist_recording_generic",
    "artist_recording_credited",
    "artist_release_generic",
    "artist_release_credited",
    "artist_releasegroup_generic",
    "artist_releasegroup_credited",
    "artist_work_generic",
]

relationship_queries = {
    "recording_work_performance": """
        UNWIND $batch AS rel
        MATCH (w:Work {id: rel.work_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (r)-[:IS_PERFORMANCE_OF]->(w)
    """,
    "recording_release_contained": """
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (rel_n:Release {id: rel.release_id})
        MERGE (r)-[:IS_CONTAINED_ON {
            media_index: rel.media_index, 
            media_id: rel.media_id, 
            track_index: rel.track_index, 
            track_id: rel.track_id
        }]->(rel_n)
    """,
    "recording_release_sample": """
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (rel_n:Release {id: rel.release_id})
        MERGE (r)-[:SAMPLES]->(rel_n)
    """,
    "recording_recording_sample": """
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (r2:Recording {id: rel.recording_2_id})
        MERGE (r)-[:SAMPLES]->(r2)
    """,
    "release_releasegroup_instance": """
        UNWIND $batch AS rel
        MATCH (r:Release {id: rel.release_id})
        MATCH (rg:ReleaseGroup {id: rel.release_group_id})
        MERGE (r)-[:IS_INSTANCE_OF]->(rg)
    """,
    "artist_artist_generic": """
        UNWIND $batch AS rel
        MATCH (a1:Artist {id: rel.artist_1_id})
        MATCH (a2:Artist {id: rel.artist_2_id})
        MERGE (a1)-[edge:IS_RELATED_TO]->(a2)
        SET edge.subtypes = rel.subtypes
    """,
    "artist_recording_generic": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (a)-[edge:PARTICIPATED_IN]->(r)
        SET edge.subtypes = rel.subtypes
    """,
    "artist_recording_credited": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """,
    "artist_release_generic": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Release {id: rel.release_id})
        MERGE (a)-[edge:PARTICIPATED_IN]->(r)
        SET edge.subtypes = rel.subtypes
    """,
    "artist_release_credited": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Release {id: rel.release_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """,
    "artist_releasegroup_generic": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:ReleaseGroup {id: rel.release_group_id})
        MERGE (a)-[edge:PARTICIPATED_IN]->(r)
        SET edge.subtypes = rel.subtypes
    """,
    "artist_releasegroup_credited": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:ReleaseGroup {id: rel.release_group_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """,
    "artist_work_generic": """
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (w:Work {id: rel.work_id})
        MERGE (a)-[edge:PARTICIPATED_IN]->(w)
        SET edge.subtypes = rel.subtypes
    """,
}

# ==========================================
# 3. GERENCIADOR DE FILAS (SINCRONIZAÇÃO)
# ==========================================

entity_batches = {}
for entity in entities:
    entity_batches[entity] = []

relationship_batches = {}
for relationship in relationships:
    relationship_batches[relationship] = []

def flush_batches(session, force=False):
    # Verifica se alguma lista atingiu o limite (ou se fomos forçados a esvaziar no fim do loop)
    if force or any(len(lst) >= BATCH_SIZE for lst in entity_batches.values()) or any(len(lst) >= BATCH_SIZE for lst in relationship_batches.values()):
        
        for entity, batch in entity_batches.items():
            session.execute_write(get_batch_insert_function(entity_queries[entity]), batch)
        
        for relationship, batch in relationship_batches.items():
            session.execute_write(get_batch_insert_function(relationship_queries[relationship]), batch)

        for key in entity_batches:
            entity_batches[key].clear()

        for key in relationship_batches:
            relationship_batches[key].clear()


# ==========================================
# 4. LEITURA DE ARQUIVOS (.TAR.XZ)
# ==========================================
for tar in ["dumps/artist.tar.xz", "dumps/work.tar.xz", "dumps/release.tar.xz", "dumps/recording.tar.xz", "dumps/release-group.tar.xz"]:
    if not (isfile(tar) and tarfile.is_tarfile(tar)):
        print(tar, "is missing! Aborting to prevent bad surprises...")
        sys.exit()

def iter_in_file(tar_name, file_name):
    xz_call = subprocess.Popen(["xz", "-dc", "-T10", tar_name], stdout=subprocess.PIPE)
    tar_call = subprocess.Popen(["tar", "-xO", "--file=-", file_name], stdin=xz_call.stdout, stdout=subprocess.PIPE)
    xz_call.stdout.close()

    for index, line_bytes in enumerate(tar_call.stdout):
        yield index, json.loads(line_bytes)

    tar_call.stdout.close()
    tar_call.wait()
    xz_call.wait()


# ==========================================
# 5. PIPELINE DE DADOS (O LOOP PRINCIPAL)
# ==========================================
with driver.session() as session:
    
    # --- 5.1 ARTISTAS ---
    print("Processando Artistas...")
    for index, dict_ in tqdm(iter_in_file("dumps/artist.tar.xz", "mbdump/artist"), total=2875751):
        life = dict_.get("life-span", {})
        entity_batches['artist'].append({
            "name": dict_.get("name"), "id": dict_.get("id"),
            "begin": life.get("begin"), "end": life.get("end"), "ended": life.get("ended")
        })
        flush_batches(session)
    flush_batches(session, force=True) # Esvazia sobras

    # --- 5.2 OBRAS (WORKS) ---
    print("Processando Obras...")
    for index, dict_ in tqdm(iter_in_file("dumps/work.tar.xz", "mbdump/work"), total=2734379):
        entity_batches['work'].append({"id": dict_.get("id"), "title": dict_.get("title"), "type": dict_.get("type")})
        flush_batches(session)
    flush_batches(session, force=True)


    # --- 5.3 RELEASE GROUPS ---
    print("Processando Release Groups...")
    for index, dict_ in tqdm(iter_in_file("dumps/release-group.tar.xz", "mbdump/release-group"), total=4448821):
        rg_id = dict_.get("id")
        rg_date = dict_.get("first-release-date")
        if not datetime_valid(rg_date):
            rg_date = None
        entity_batches['releasegroup'].append({"id": rg_id, "title": dict_.get("title"), "first-release-date": rg_date, "primary-type": dict_.get("primary-type"), "secondary-types": dict_.get("secondary-types")})
        for credited in dict_.get("artist-credit", []):
            if credited.get("artist"):
                relationship_batches["artist_releasegroup_credited"].append({"artist_id": credited["artist"].get("id"), "release_group_id": rg_id, "subtype": "credited"})

                    
        flush_batches(session)
    flush_batches(session, force=True)

    # --- 5.4 LANÇAMENTOS E SUAS RELAÇÕES TOTAIS ---
    print("Processando Lançamentos, Grupos, Gravações e Arestas Triviais...")
    for index, dict_ in tqdm(iter_in_file("dumps/release.tar.xz", "mbdump/release"), total=4774602):
        release_id = dict_.get("id")
        date = dict_.get("date")
        # 1. Adicionar Release
        if not datetime_valid(date):
            date = None

        entity_batches["release"].append({"id": release_id, "title": dict_.get("title"), "date": date, "status": dict_.get("status")})
        for credited in dict_.get("artist-credit", []):
            if credited.get("artist"):
                relationship_batches["artist_release_credited"].append({"artist_id": credited["artist"].get("id"), "release_id": release_id, "subtype": "credited"})
        
        # 2. Adicionar Release Group e a relação Release -> RG
        if "release-group" in dict_:
            rg = dict_["release-group"]
            rg_id = rg.get("id")
            relationship_batches["release_releasegroup_instance"].append({"release_id": release_id, "release_group_id": rg_id})

        # 3. Adicionar Recordings e relações
        for media_index, media in enumerate(dict_.get("media", [])):
            for track_index, track in enumerate(media.get("tracks", [])):
                recording = track.get("recording")
                if recording:
                    rec_id = recording.get("id")
                    entity_batches['recording'].append({"id": rec_id, "title": recording.get("title")})
                    relationship_batches["recording_release_contained"].append({
                        "recording_id": rec_id, 
                        "release_id": release_id,
                        "media_index": media_index, 
                        "media_id": media["id"], 
                        "track_index": track_index,
                        "track_id": track["id"]
                    })
                    
                    # 4. Relações da recording com Work, recording e release group dentro das propriedades do recording
                    for rel in recording.get("relations", []):
                        if rel.get("target-type") == "work": #um performance aqui seria redundante tb
                            work = rel.get("work")
                            if work:
                                relationship_batches["recording_work_performance"].append({"work_id": work.get("id"), "recording_id": rec_id})
                        elif rel.get("target-type") == "recording" and rel.get("type") == "samples material" and rel.get("direction") == "forward": #samples material redundante
                            recording_2 = rel.get("recording")
                            if recording_2:
                                relationship_batches["recording_recording_sample"].append({"recording_id": recording.get("id"), "recording_2_id": recording_2.get("id")})
                        elif rel.get("target-type") == "release" and rel.get("type") == "samples material": #samples material redundante
                            release = rel.get("release")
                            if release:
                                relationship_batches["recording_release_sample"].append({"recording_id": recording.get("id"), "release_id": release.get("id")})
                    
                    # 5. Artist Credits
                    for credited in recording.get("artist-credit", []):
                        if credited.get("artist"):
                            relationship_batches["artist_recording_credited"].append({"artist_id": credited["artist"].get("id"), "recording_id": rec_id, "subtype": "credited"})

        flush_batches(session)
    flush_batches(session, force=True)

    # --- 5.5 GRAVAÇÕES EXTRAS (Tratando as órfãs) ---
    print("Processando Gravações Órfãs do arquivo de Recordings...")
    for index, dict_ in tqdm(iter_in_file("dumps/recording.tar.xz", "mbdump/recording"), total=133144):
        rec_id = dict_.get("id")
        entity_batches['recording'].append({"id": rec_id, "title": dict_.get("title")})
        
        for rel in dict_.get("relations", []):
            if rel.get("target-type") == "work":
                work = rel.get("work")
                if work:
                    relationship_batches["recording_work_performance"].append({"work_id": work.get("id"), "recording_id": rec_id})
            elif rel.get("target-type") == "recording" and rel.get("type") == "samples material" and rel.get("direction") == "forward":
                recording_2 = rel.get("recording")
                if recording_2:
                    relationship_batches["recording_recording_sample"].append({"recording_id": recording.get("id"), "recording_2_id": recording_2.get("id")})
            elif rel.get("target-type") == "release" and rel.get("type") == "samples material":
                release = rel.get("release")
                if release:
                    relationship_batches["recording_release_sample"].append({"recording_id": recording.get("id"), "release_id": release.get("id")})


        flush_batches(session)
    flush_batches(session, force=True)

# --- 5.6 RELAÇÕES ENTRE ARTISTAS E TUDO ---
    print("Processando Artistas...")
    
    for index, dict_ in tqdm(iter_in_file("dumps/artist.tar.xz", "mbdump/artist"), total=2875751):
        artist_relationships = {
            "artist": defaultdict(lambda: []),
            "recording": defaultdict(lambda: []),
            "release": defaultdict(lambda: []),
            "releasegroup": defaultdict(lambda: []),
            "work": defaultdict(lambda: []),
        }
        for relation in dict_.get("relations", []):
            target_type = relation.get("target-type")
            rel_type = relation.get("type")
            counterpart = relation.get(target_type)
            if target_type in entities and counterpart and (target_type != "artist" or relation.get("direction") == "forward"):
                artist_relationships[target_type][counterpart.get("id")].append(rel_type)

            # if target_type == "artist" and relation.get("direction") == "forward":
            #     relationship_batches["artist_artist_generic"].append({"artist_1_id": dict_.get("id"), "artist_2_id": relation.get("artist", {}).get("id"), "subtype": rel_type})
            
            # elif target_type == "recording":
            #     relationship_batches["artist_recording_generic"].append({"artist_id": dict_.get("id"), "recording_id": relation.get("recording", {}).get("id"), "subtype": rel_type})

            # elif target_type == "release":
            #     relationship_batches["artist_release_generic"].append({"artist_id": dict_.get("id"), "release_id": relation.get("release", {}).get("id"), "subtype": rel_type})

            # elif target_type == "release-group":
            #     relationship_batches["artist_releasegroup_generic"].append({"artist_id": dict_.get("id"), "release_group_id": relation.get("release-group", {}).get("id"), "subtype": rel_type})

            # elif target_type == "work":
            #     relationship_batches["artist_work_generic"].append({"artist_id": dict_.get("id"), "work_id": relation.get("work", {}).get("id"), "subtype": rel_type})
        
        for entity, counterparts in artist_relationships.items():
            for counterpart_id, subtypes in counterparts.items():
                if entity == "artist":
                    relationship_batches[f"artist_{entity}_generic"].append({"artist_1_id": dict_.get("id"), "artist_2_id": counterpart_id, "subtypes": subtypes})
                else:
                    relationship_batches[f"artist_{entity}_generic"].append({"artist_id": dict_.get("id"), f"{entity}_id": counterpart_id, "subtypes": subtypes})

        flush_batches(session)
    flush_batches(session, force=True) # Esvazia sobras

print("Importação base do Neo4j finalizada com sucesso!")
