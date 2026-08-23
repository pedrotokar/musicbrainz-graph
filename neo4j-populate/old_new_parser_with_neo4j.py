from neo4j import GraphDatabase
from tqdm import tqdm
import tarfile
import subprocess
from os.path import isfile
import json
from datetime import datetime


relation_manual = {"artist": {
    "artist": {
        "member of band": "IS_MEMBER_OF",
        "subgroup": "IS_SUBGROUP_OF",
        "artist rename": "WAS_RENAMED_INTO",
        "artistic director": "IS_ARTISTIC_DIRECTOR",
        "conductor position": "IS_CONDUCTOR",
        "founder": "IS_FOUNDER",
        "supporting musician": "IS_SUPPORTING_ARTIST_FOR",
            "vocal supporting musician": "IS_SUPPORTING_VOCALIST",
            "instrumental supporting musician": "IS_SUPPORTING_INSTRUMENTALIST",
        "tribute": "IS_TRIBUTE_TO",
        "voice actor": "IS_VOICE_ACTOR_OF",
        "collaboration": "COLLABORATED_WITH",
        "is person": "IS",
        "teacher": "TAUGHT",
        "artist-in-residence": "WAS_AN_ARTIST_IN_RESIDENCE_AT",
            "composer-in-residence": "WAS_A_COMPOSER_IN_RESIDENCE_AT",
        }
    }
}


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

# Inserção de entidades
# def add_artist_batch(tx, batch):
#     tx.run("""
#         UNWIND $batch AS data
#         MERGE (n:Artist {id: data.id})
#         ON CREATE SET n.name = data.name, n.begin = data.begin, n.end = data.end, n.ended = data.ended, n.type = data.type
#     """, batch=batch)

# def add_work_batch(tx, batch):
#     tx.run("""
#         UNWIND $batch AS data
#         MERGE (n:Work {id: data.id})
#         ON CREATE SET n.title = data.title, n.type = data.type
#     """, batch=batch)

# def add_release_batch(tx, batch):
#     tx.run("""
#         UNWIND $batch AS data
#         MERGE (n:Release {id: data.id})
#         ON CREATE SET n.title = data.title, n.release_date = date(data.date), n.status = data.status
#     """, batch=batch)

# def add_release_group_batch(tx, batch):
#     tx.run("""
#         UNWIND $batch AS data
#         MERGE (n:ReleaseGroup {id: data.id})
#         ON CREATE SET n.title = data.title, n.type = data.`primary-type`, n.first_release_date = date(data.`first-release-date`)
#     """, batch=batch)

# def add_recording_batch(tx, batch):
#     tx.run("""
#         UNWIND $batch AS data
#         MERGE (n:Recording {id: data.id})
#         ON CREATE SET n.title = data.title
#     """, batch=batch)

def add_artist_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS data
        MERGE (n:Artist {id: data.id})
        SET n.name = coalesce(data.name, n.name), 
            n.begin = coalesce(data.begin, n.begin), 
            n.end = coalesce(data.end, n.end), 
            n.ended = coalesce(data.ended, n.ended), 
            n.type = coalesce(data.type, n.type)
    """, batch=batch)

def add_work_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS data
        MERGE (n:Work {id: data.id})
        SET n.title = coalesce(data.title, n.title), 
            n.type = coalesce(data.type, n.type)
    """, batch=batch)

def add_release_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS data
        MERGE (n:Release {id: data.id})
        SET n.title = coalesce(data.title, n.title), 
            n.release_date = coalesce(date(data.date), n.release_date), 
            n.status = coalesce(data.status, n.status)
    """, batch=batch)

def add_release_group_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS data
        MERGE (n:ReleaseGroup {id: data.id})
        SET n.title = coalesce(data.title, n.title),
            n.type = coalesce(data["primary-type"], n.type),
            n.secondary_types = coalesce(data["secondary-types"], n.secondary_types),
            n.first_release_date = coalesce(date(data["first-release-date"]), n.first_release_date)
    """, batch=batch)

def add_recording_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS data
        MERGE (n:Recording {id: data.id})
        SET n.title = coalesce(data.title, n.title)
    """, batch=batch)


# Inserção de relações

# work | recording

def add_work_recording_performance_rel_batch(tx, batch): #performance
    tx.run("""
        UNWIND $batch AS rel
        MATCH (w:Work {id: rel.work_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (r)-[:IS_PERFORMANCE_OF]->(w)
    """, batch=batch)

#recording | release

def add_recording_release_contained_rel_batch(tx, batch): #aresta trivial
    tx.run("""
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (rel_n:Release {id: rel.release_id})
        MERGE (r)-[:IS_CONTAINED_ON {
            media_index: rel.media_index, 
            media_id: rel.media_id, 
            track_index: rel.track_index, 
            track_id: rel.track_id
        }]->(rel_n)
    """, batch=batch)

def add_recording_release_samples_rel_batch(tx, batch): #sampling
    tx.run("""
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (rel_n:Release {id: rel.release_id})
        MERGE (r)-[:SAMPLES]->(rel_n)
    """, batch=batch)

# recording | recording

def add_recording_recording_samples_rel_batch(tx, batch): #sampling
    tx.run("""
        UNWIND $batch AS rel
        MATCH (r:Recording {id: rel.recording_id})
        MATCH (r2:Recording {id: rel.recording_2_id})
        MERGE (r)-[:SAMPLES]->(r2)
    """, batch=batch)


# release | release group

def add_release_release_group_instance_rel_batch(tx, batch): #aresta trivial
    tx.run("""
        UNWIND $batch AS rel
        MATCH (r:Release {id: rel.release_id})
        MATCH (rg:ReleaseGroup {id: rel.release_group_id})
        MERGE (r)-[:IS_INSTANCE_OF]->(rg)
    """, batch=batch)

# artist | artist

def add_artist_artist_generic_rel_batch(tx, batch, relation_type):
    tx.run(f"""
        UNWIND $batch AS rel
        MATCH (a1:Artist {{id: rel.artist_1_id}})
        MATCH (a2:Artist {{id: rel.artist_2_id}})
        MERGE (a1)-[:{relation_type}]->(a2)
    """, batch = batch)

# artist | recording

def add_artist_recording_generic_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (a)-[:PARTICIPATED_IN {subtype: rel.subtype}]->(r)
    """, batch = batch)

def add_artist_recording_credited_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Recording {id: rel.recording_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """, batch = batch)

# artist | release

def add_artist_release_generic_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Release {id: rel.release_id})
        MERGE (a)-[:PARTICIPATED_IN {subtype: rel.subtype}]->(r)
    """, batch = batch)

def add_artist_release_credited_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:Release {id: rel.release_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """, batch = batch)

# artist | release group

def add_artist_release_group_generic_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:ReleaseGroup {id: rel.release_group_id})
        MERGE (a)-[:PARTICIPATED_IN {subtype: rel.subtype}]->(r)
    """, batch = batch)
    
def add_artist_release_group_credited_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (r:ReleaseGroup {id: rel.release_group_id})
        MERGE (a)-[:CREDITED_IN]->(r)
    """, batch = batch)

# artist | work

def add_artist_work_generic_rel_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS rel
        MATCH (a:Artist {id: rel.artist_id})
        MATCH (w:Work {id: rel.work_id})
        MERGE (a)-[:PARTICIPATED_IN {subtype: rel.subtype}]->(w)
    """, batch = batch)


# ==========================================
# 3. GERENCIADOR DE FILAS (SINCRONIZAÇÃO)
# ==========================================
batches = {
    'artist': [], 'work': [], 'release': [], 'release_group': [], 'recording': [],
    'rel_w_r': [], 'rel_r_rel': [], 'rel_rel_rg': [], "rel_r_r_sample": [], "rel_r_rel_sample": [],
    'artist_r_rel': [], 'artist_rel_rel': [], 'artist_rg_rel': [], 'artist_w_rel': [],
    'artist_r_rel_cred': [], 'artist_rel_rel_cred': [], 'artist_rg_rel_cred': []
}

for key in relation_manual["artist"]["artist"]:
    batches[f"artist-artist-{key}"] = []

def flush_batches(session, force=False):
    # Verifica se alguma lista atingiu o limite (ou se fomos forçados a esvaziar no fim do loop)
    if force or any(len(lst) >= BATCH_SIZE for lst in batches.values()):
        
        # 1º PASSO: Nós sempre descem primeiro para evitar nós fantasmas
        if batches['artist']: session.execute_write(add_artist_batch, batches['artist'])
        if batches['work']: session.execute_write(add_work_batch, batches['work'])
        if batches['release']: session.execute_write(add_release_batch, batches['release'])
        if batches['release_group']: session.execute_write(add_release_group_batch, batches['release_group'])
        if batches['recording']: session.execute_write(add_recording_batch, batches['recording'])
        
        # 2º PASSO: Com os nós no banco, inserimos as relações
        if batches['rel_w_r']: session.execute_write(add_work_recording_performance_rel_batch, batches['rel_w_r'])
        if batches['rel_r_rel']: session.execute_write(add_recording_release_contained_rel_batch, batches['rel_r_rel'])
        if batches['rel_rel_rg']: session.execute_write(add_release_release_group_instance_rel_batch, batches['rel_rel_rg'])
        if batches["rel_r_r_sample"]: session.execute_write(add_recording_recording_samples_rel_batch, batches["rel_r_r_sample"])    
        if batches["rel_r_rel_sample"]: session.execute_write(add_recording_release_samples_rel_batch, batches["rel_r_rel_sample"])
        if batches["artist_r_rel"]: session.execute_write(add_artist_recording_generic_rel_batch, batches["artist_r_rel"])
        if batches["artist_rel_rel"]: session.execute_write(add_artist_release_generic_rel_batch, batches["artist_rel_rel"])
        if batches["artist_rg_rel"]: session.execute_write(add_artist_release_group_generic_rel_batch, batches["artist_rg_rel"])
        if batches["artist_w_rel"]: session.execute_write(add_artist_work_generic_rel_batch, batches["artist_w_rel"])
        if batches["artist_r_rel_cred"]: session.execute_write(add_artist_recording_credited_rel_batch, batches["artist_r_rel_cred"])
        if batches["artist_rel_rel_cred"]: session.execute_write(add_artist_release_credited_rel_batch, batches["artist_rel_rel_cred"])
        if batches["artist_rg_rel_cred"]: session.execute_write(add_artist_release_group_credited_rel_batch, batches["artist_rg_rel_cred"])

        for key in relation_manual["artist"]["artist"]:
            if batches[f"artist-artist-{key}"]: session.execute_write(add_artist_artist_generic_rel_batch, batches[f"artist-artist-{key}"], relation_manual["artist"]["artist"][key])

        # 3º PASSO: Limpar todas as listas da memória
        for key in batches:
            batches[key].clear()


# ==========================================
# 4. LEITURA DE ARQUIVOS (.TAR.XZ)
# ==========================================
for tar in ["data/artist.tar.xz", "data/work.tar.xz", "data/release.tar.xz", "data/recording.tar.xz", "data/release-group.tar.xz"]:
    if not (isfile(tar) and tarfile.is_tarfile(tar)):
        print(tar, "is missing! Aborting to prevent bad surprises...")
        exit()

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
    for index, dict_ in tqdm(iter_in_file("data/artist.tar.xz", "mbdump/artist"), total=2875751):
        life = dict_.get("life-span", {})
        batches['artist'].append({
            "name": dict_.get("name"), "id": dict_.get("id"),
            "begin": life.get("begin"), "end": life.get("end"), "ended": life.get("ended")
        })
        flush_batches(session)
    flush_batches(session, force=True) # Esvazia sobras

    # --- 5.2 OBRAS (WORKS) ---
    print("Processando Obras...")
    for index, dict_ in tqdm(iter_in_file("data/work.tar.xz", "mbdump/work"), total=2734379):
        batches['work'].append({"id": dict_.get("id"), "title": dict_.get("title"), "type": dict_.get("type")})
        flush_batches(session)
    flush_batches(session, force=True)


    # --- 5.3 RELEASE GROUPS ---
    print("Processando Release Groups...")
    for index, dict_ in tqdm(iter_in_file("data/release-group.tar.xz", "mbdump/release-group"), total=4448821):
        rg_id = dict_.get("id")
        rg_date = dict_.get("first-release-date")
        if not datetime_valid(rg_date):
            rg_date = None
        batches['release_group'].append({"id": rg_id, "title": dict_.get("title"), "first-release-date": rg_date, "primary-type": dict_.get("primary-type"), "secondary-types": dict_.get("secondary-types")})
        for credited in dict_.get("artist-credit", []):
            if credited.get("artist"):
                batches["artist_rg_rel_cred"].append({"artist_id": credited["artist"].get("id"), "release_group_id": rg_id, "subtype": "credited"})

                    
        flush_batches(session)
    flush_batches(session, force=True)

    # --- 5.3 LANÇAMENTOS E SUAS RELAÇÕES TOTAIS ---
    print("Processando Lançamentos, Grupos, Gravações e Arestas Triviais...")
    for index, dict_ in tqdm(iter_in_file("data/release.tar.xz", "mbdump/release"), total=4774602):
        release_id = dict_.get("id")
        date = dict_.get("date")
        # 1. Adicionar Release
        if not datetime_valid(date):
            date = None

        batches['release'].append({"id": release_id, "title": dict_.get("title"), "date": date, "status": dict_.get("status")})
        for credited in dict_.get("artist-credit", []):
            if credited.get("artist"):
                batches["artist_rel_rel_cred"].append({"artist_id": credited["artist"].get("id"), "release_id": release_id, "subtype": "credited"})
        
        # 2. Adicionar Release Group e a relação Release -> RG
        if "release-group" in dict_:
            rg = dict_["release-group"]
            rg_id = rg.get("id")
            batches['rel_rel_rg'].append({"release_id": release_id, "release_group_id": rg_id})

        # 3. Adicionar Recordings e relações
        for media_index, media in enumerate(dict_.get("media", [])):
            for track_index, track in enumerate(media.get("tracks", [])):
                recording = track.get("recording")
                if recording:
                    rec_id = recording.get("id")
                    batches['recording'].append({"id": rec_id, "title": recording.get("title")})
                    batches['rel_r_rel'].append({
                        "recording_id": rec_id, 
                        "release_id": release_id,
                        "media_index": media_index, 
                        "media_id": media["id"], 
                        "track_index": track_index,
                        "track_id": track["id"]
                    })
                    
                    # 4. Relações da recording com Work, recording e release group dentro das propriedades do recording
                    for rel in recording.get("relations", []):
                        if rel.get("target-type") == "work":
                            work = rel.get("work")
                            if work:
                                batches['rel_w_r'].append({"work_id": work.get("id"), "recording_id": rec_id})
                        elif rel.get("target-type") == "recording" and rel.get("type") == "samples material" and rel.get("direction") == "forward":
                            recording_2 = rel.get("recording")
                            if recording_2:
                                batches["rel_r_r_sample"].append({"recording_id": recording.get("id"), "recording_2_id": recording_2.get("id")})
                        elif rel.get("target-type") == "release" and rel.get("type") == "samples material":
                            release = rel.get("release")
                            if release:
                                batches["rel_r_rel_sample"].append({"recording_id": recording.get("id"), "release_id": release.get("id")})
                    
                    # 5. Artist Credits
                    for credited in recording.get("artist-credit", []):
                        if credited.get("artist"):
                            batches["artist_r_rel_cred"].append({"artist_id": credited["artist"].get("id"), "recording_id": rec_id, "subtype": "credited"})

        flush_batches(session)
    flush_batches(session, force=True)

    # --- 5.4 GRAVAÇÕES EXTRAS (Tratando as órfãs) ---
    print("Processando Gravações Órfãs do arquivo de Recordings...")
    for index, dict_ in tqdm(iter_in_file("data/recording.tar.xz", "mbdump/recording"), total=133144):
        rec_id = dict_.get("id")
        batches['recording'].append({"id": rec_id, "title": dict_.get("title")})
        
        for rel in dict_.get("relations", []):
            if rel.get("target-type") == "work":
                work = rel.get("work")
                if work:
                    batches['rel_w_r'].append({"work_id": work.get("id"), "recording_id": rec_id})
            elif rel.get("target-type") == "recording" and rel.get("type") == "samples material" and rel.get("direction") == "forward":
                recording_2 = rel.get("recording")
                if recording_2:
                    batches["rel_r_r_sample"].append({"recording_id": dict_.get("id"), "recording_2_id": recording_2.get("id")})
            elif rel.get("target-type") == "release" and rel.get("type") == "samples material":
                release = rel.get("release")
                if release:
                    batches["rel_r_rel_sample"].append({"recording_id": rec_id, "release_id": release.get("id")})

                    
        flush_batches(session)
    flush_batches(session, force=True)

# --- 5.2 RELAÇÕES ENTRE ARTISTAS E TUDO ---
    print("Processando Artistas...")
    relation_dict = relation_manual.get("artist", {}).get("artist", {})
    
    for index, dict_ in tqdm(iter_in_file("data/artist.tar.xz", "mbdump/artist"), total=2875751):
        for relation in dict_.get("relations", []):
            target_type = relation.get("target-type")
            rel_type = relation.get("type")
            
            if target_type == "artist" and relation.get("direction") == "forward" and rel_type in relation_dict:
                batches[f"artist-artist-{rel_type}"].append({"artist_1_id": dict_.get("id"), "artist_2_id": relation.get("artist", {}).get("id")})
            
            elif target_type == "recording":
                batches["artist_r_rel"].append({"artist_id": dict_.get("id"), "recording_id": relation.get("recording", {}).get("id"), "subtype": rel_type})

            elif target_type == "release":
                batches["artist_rel_rel"].append({"artist_id": dict_.get("id"), "release_id": relation.get("release", {}).get("id"), "subtype": rel_type})

            elif target_type == "release-group":
                batches["artist_rg_rel"].append({"artist_id": dict_.get("id"), "release_group_id": relation.get("release-group", {}).get("id"), "subtype": rel_type})

            elif target_type == "work":
                batches["artist_w_rel"].append({"artist_id": dict_.get("id"), "work_id": relation.get("work", {}).get("id"), "subtype": rel_type})
        
        flush_batches(session)
    flush_batches(session, force=True) # Esvazia sobras

print("Importação base do Neo4j finalizada com sucesso!")
