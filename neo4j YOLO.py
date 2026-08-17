#ideia:
# função de adicionar nó (recebe dados do nó brutos, uma função que mapeia para propriedaes no modelo via strategy)
# e uma label de qual o tipo

from neo4j import GraphDatabase
from neo4j.exceptions import ConstraintError

#progress bar
from tqdm import tqdm
#File opening
import tarfile
import subprocess
from os.path import isfile
#Data processing
import json
import orjson
from collections import defaultdict
from pprint import pprint
import sys


URI = "neo4j://localhost"
AUTH = ("neo4j", "neo4j")

driver = GraphDatabase.driver(URI, auth = AUTH)
driver.verify_connectivity()

# driver.execute_query("""
# CREATE CONSTRAINT artistas_id_unico FOR (n:Artist) REQUIRE n.id IS UNIQUE
# """)

# driver.execute_query("""
# CREATE CONSTRAINT works_id_unico FOR (n:Work) REQUIRE n.id IS UNIQUE
# """)


driver.execute_query("""
CREATE CONSTRAINT release_id_unico FOR (n:Release) REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT release_group_id_unico FOR (n:ReleaseGroup) REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT recording_id_unico FOR (n:Recording) REQUIRE n.id IS UNIQUE
""")

def add_artist_batch(tx, batch):
    query = """
        UNWIND $batch AS artist
        MERGE (a:Artist {id: artist.id})
        ON CREATE SET 
            a.name = artist.name, 
            a.begin = artist.begin, 
            a.end = artist.end, 
            a.ended = artist.ended
    """
    tx.run(query, batch=batch)

def add_work_batch(tx, batch):
    query = """
        UNWIND $batch AS work
        MERGE (w:Work {id: work.id})
        ON CREATE SET w.title = work.title
    """
    tx.run(query, batch=batch)

def add_release_batch(tx, batch):
    query = """
        UNWIND $batch AS release
        MERGE (r:Release {id: release.id})
        ON CREATE SET r.title = release.title
    """
    tx.run(query, batch=batch)

def add_release_group_batch(tx, batch):
    query = """
        UNWIND $batch AS release_group
        MERGE (rg:ReleaseGroup {id: release_group.id})
        ON CREATE SET rg.title = release_group.title
    """
    tx.run(query, batch=batch)

def add_recording_batch(tx, batch):
    query = """
        UNWIND $batch AS recording
        MERGE (r:Recording {id: recording.id})
        ON CREATE SET r.title = recording.title
    """
    tx.run(query, batch=batch)
    
def add_work_recording_relation(work, recording):
    driver.execute_query("""
        MATCH (a1:Work {id: $work_id})
        MATCH (a2:Recording {id: $recording_id})
        MERGE (a1)-[:IS_PERFORMANCE_OF]->(a2)
    """, 
    work_id = work["id"],
    recording_id = recording["id"]
    )

def add_recording_release_relation(recording, release):
    driver.execute_query("""
        MATCH (a1:Recording {id: $recording_id})
        MATCH (a2:Release {id: $release_id})
        MERGE (a1)-[:IS_PART_OF]->(a2)
    """, 
    recording_id = recording["id"],
    release_id = release["id"]
    )

def add_release_release_group_relation(release, release_group):
    driver.execute_query("""
        MATCH (a1:Release {id: $release_id})
        MATCH (a2:ReleaseGroup {id: $release_group_id})
        MERGE (a1)-[:IS_INSTANCE_OF]->(a2)
    """, 
    release_id = release["id"],
    release_group_id = release_group["id"]
    )

def add_artist_artist_relation(artist_1_id, artist_2_id, rtype):
    driver.execute_query(f"""
        MATCH (a1:Artist {{id: $artist_1_id}})
        MATCH (a2:Artist {{id: $artist_2_id}})
        MERGE (a1)-[:{rtype}]->(a2)
    """, 
    artist_1_id = artist_1_id,
    artist_2_id = artist_2_id
    )

def add_ignore_constraint(function, object_):
    function(object_)

# summary = driver.execute_query("""
#     CREATE (a:Band {name: $name})
#     CREATE (b:Band {name: $otherBandName})
#     CREATE (a)-[:COLABORATED]->(b)
#     """,
#     name = "Guns N Roses",
#     otherBandName = "Skid Row",
#     database = "music-explorer"
# ).summary


# print("Created {nodes_created} nodes in {time} ms.".format(
#     nodes_created=summary.counters.nodes_created,
#     time=summary.result_available_after
# ))



#Helper dictionaries and outputs

artist_map = dict()
work_map = dict()

#It isnt possible to safely open the file with native python tools because
#we get a buffer in which we cant use seek, and so the python standard features
#to iter in the buffer will error out. So the approach is to use shell commands.
#they are wrapped here into an iterator to convenience

for tar in ["data/artist.tar.xz", "data/work.tar.xz", "data/release.tar.xz", "data/recording.tar.xz"]:
    if not (isfile(tar) and tarfile.is_tarfile(tar)):
        print(tar, "is missing! Aborting to prevent bad surprises...")
        exit()

def iter_in_file(tar_name, file_name):
    if not tarfile.is_tarfile(tar_name):
        print(tar_name, "isn't a tar xz file!")
        exit()
    xz_call = subprocess.Popen(
        ["xz", "-dc", "-T10", tar_name], #The command here is xz --decompress --stdout "tar file"
        stdout = subprocess.PIPE
    )

    tar_call = subprocess.Popen(
        ["tar", "-xO", "--file=-", file_name], #The command here is tar -x0 --file="the file inside thar"
        stdin = xz_call.stdout,
        stdout = subprocess.PIPE
    )

    xz_call.stdout.close()

#    while True:
#        line = tar_call.stdout.readline()
    for index, line_bytes in enumerate(tar_call.stdout):
        line = line_bytes.decode("utf-8", errors = "replace").rstrip("\n")
        dictionary = json.loads(line_bytes)
        yield index, dictionary

    print("Closing subprocesses and pipes")
    tar_call.stdout.close()
    tar_call.wait()
    xz_call.wait()

autorship = ["autorship", "writer", "composer", "lyricist", "librettist", "revised by", "scriptwriter", "translator", "reconstructed by", "arranger", "instrument arranger", "orchestrator", "vocal arranger", "adapter", "previous attribution"]
performance = ["performance", "performer", "instrument", "vocal", "performing orchestra", "conductor", "chorus master", "concertmaster", "audio director"]

for index, dictionary in tqdm(iter_in_file("data/artist.tar.xz", "mbdump/artist"), total = 2875751):
    # if index > 1:
        # break
    if True:
        entry = {
            "n": dictionary["name"],
            "r": False,
            "c": 0,
            "ms": set(), #members
            "im": set(), #member of
            "cs": defaultdict(lambda: [5000, set()]), #covers someone
            "gc": set(), #got covered by someone
        }

        #TODO: ADICIONAR NO NEO4J
        add_ignore_constraint(add_artist, dictionary)

        for relation in dictionary["relations"]:
            if relation["target-type"] == "artist" and relation["type"] == "tribute" and relation["direction"] == "forward" and not relation["ended"]:
                entry["r"] = True #mark for remotion
                # pprint(relation)
            if relation["target-type"] == "artist" and relation["type"] == "member of band":
                if relation["direction"] == "forward":
                    entry["im"].add(relation["artist"]["id"])
                elif relation["direction"] == "backward":
                    entry["ms"].add(relation["artist"]["id"])
        artist_map[dictionary["id"]] = entry

for index, dictionary in tqdm(iter_in_file("data/work.tar.xz", "mbdump/work"), total = 2734379):
    # if index > 0:
    #     break
    if True:
        entry = {
            "n": dictionary["title"],
            "a": defaultdict(lambda: 0)
        }
        #TODO: ADICIONAR NO NEO4J
        add_ignore_constraint(add_work(dictionary))
        # Old code that badly got work autorship
        # for relation in dictionary["relations"]:
        #     if relation["type"] in autorship:
        #         entry["a"].add(relation["artist"]["id"])
        work_map[dictionary["id"]] = entry

#map works to authors - different logic than just seeing relations to capture bands and such
for index, dictionary in tqdm(iter_in_file("data/release.tar.xz", "mbdump/release"), total = 4774602):

    add_ignore_constraint(add_release, dictionary)
    if dictionary.get("release-group", None):
        add_ignore_constraint(add_release_group, dictionary["release-group"])

    for media in dictionary.get("media", []):
        for track in media.get("tracks", []):
            if track.get("recording", None):
                add_ignore_constraint(add_recording, track["recording"])
            for relation in track["recording"]["relations"]:
                if relation.get("target-type", None) == "work":        #!
                    add_work_recording_relation(relation["work"], track) #!
                if relation["target-type"] == "work" and not ("cover" in relation["attributes"]):
                    work_id = relation["work"]["id"]
                    for artist_meta in track["artist-credit"]:
                        try:
                            work_map[work_id]["a"][artist_meta["artist"]["id"]] += 1 #autorship count
                        except:
                            print(f"work error (id {work_id}), skipping")

for index, dictionary in tqdm(iter_in_file("data/recording.tar.xz", "mbdump/recording"), total = 133144):
    for relation in dictionary["relations"]:

        if relation.get("target-type", None) == "work":        #!
            add_work_recording_relation(relation["work"], dictionary) #!
        
        if relation["target-type"] == "work" and not ("cover" in relation["attributes"]):
            work_id = relation["work"]["id"]
            for artist_meta in dictionary["artist-credit"]:
                work_map[work_id]["a"][artist_meta["artist"]["id"]] += 1 #autorship count


for work in tqdm(work_map):
    total_sum = sum(work_map[work]["a"].values())
    true_authors = list()
    for artist, count in work_map[work]["a"].items():
        if count/total_sum > 0.25:
            true_authors.append(artist)
            artist_map[artist]["c"] += 1 #authoral work count
    work_map[work]["a"] = true_authors

for artist in tqdm(artist_map):
    if artist_map[artist]["c"] == 0 and len(artist_map[artist]["im"]) == 0: #doenst have authoral music and isnt member of a band
        artist_map[artist]["r"] = True #mark for remotion

#add cover edges
for index, dictionary in tqdm(iter_in_file("data/release.tar.xz", "mbdump/release"), total = 4774602):
    for media in dictionary.get("media", []):
        for track in media.get("tracks", []):
            for relation in track["recording"]["relations"]:
                if relation["target-type"] == "work" and "cover" in relation["attributes"]:
                    cover_of = relation["work"]["id"]
                    for cover_artist in track["artist-credit"]:
                        cover_artist = cover_artist["artist"]["id"]
                        if artist_map[cover_artist]["r"]: #doesnt add edges for artist that will be removed
                            continue
                        for og_artist in work_map[cover_of]["a"]: #no verification here because it wont be in any work authorship by the criterion
                            if og_artist == cover_artist:
                                continue
                            date = dictionary.get("date", "5000").split("-")[0]
                            date = int(date) if not (date in ["", "????"]) else 5000
                            artist_map[cover_artist]["cs"][og_artist][1].add(work_map[cover_of]["n"])
                            
                            artist_map[cover_artist]["cs"][og_artist][0] = min(
                                artist_map[cover_artist]["cs"][og_artist][0], #already saved cover
                                date
                            )
                            artist_map[og_artist]["gc"].add(cover_artist)
    
                            #TODO: ADICIONAR NO NEO4J
                            add_artist_artist_relation(cover_artist, og_artist, "COVERS")

for index, dictionary in tqdm(iter_in_file("data/recording.tar.xz", "mbdump/recording"), total = 133144):
    for relation in dictionary["relations"]:
        if relation["target-type"] == "work" and "cover" in relation["attributes"]:
            cover_of = relation["work"]["id"]
            for cover_artist in dictionary["artist-credit"]:
                cover_artist = cover_artist["artist"]["id"]
                if artist_map[cover_artist]["r"]: #doesnt add edges for artist that will be removed
                    continue
                for og_artist in work_map[cover_of]["a"]:
                    if og_artist == cover_artist:
                        continue
                    artist_map[cover_artist]["cs"][og_artist][1].add(work_map[cover_of]["n"])
                    artist_map[cover_artist]["cs"][og_artist][0] = min(
                        artist_map[cover_artist]["cs"][og_artist][0], #already saved cover
                        int(dictionary.get("date", "5000").split("-")[0])#this cover date
                    )
                    artist_map[og_artist]["gc"].add(cover_artist)
                    #TODO: ADICIONAR NO NEO4J
                    add_artist_artist_relation(cover_artist, og_artist, "COVERS")

    # generos = dictionary.get("genres", list())
    # if len(generos) != 0:
    #     filtered.append(dictionary)
    #     new = {
    #         "genres": generos,
    #         "life-span": dictionary["life-span"],
    #         "name": dictionary["name"]
    #     }
    #     filtered_only_features.append(new)
    #     generos = [genero["name"] for genero in dictionary["genres"]]
    #     print(generos)
    #     tem_rock = 0
    #     for genero in generos:
    #         if "rock" in genero:
    #             counts_rock[genero] += 1
    #             tem_rock = 1
    #     if tem_rock:
    #         filtered_rock.append(dictionary)

print("Writing artists map to json")
deletion_keys = []
for artist in artist_map:
    if artist_map[artist]["r"]: #see if its marked for remotion
        deletion_keys.append(artist)
        continue

    new_entry = dict()
    new_entry["n"] = artist_map[artist]["n"]
    new_entry["ms"] = list(artist_map[artist]["ms"])
    new_entry["im"] = list(artist_map[artist]["im"])
    new_entry["cs"] = dict()
    for key in artist_map[artist]["cs"]:
        new_entry["cs"][key] = []
        new_entry["cs"][key].append(artist_map[artist]["cs"][key][0])
        new_entry["cs"][key].append(list(artist_map[artist]["cs"][key][1]))
    new_entry["gc"] = list(artist_map[artist]["gc"])

    artist_map[artist] = new_entry

for artist in deletion_keys:
    del artist_map[artist]

with open("artist_map.json", "w") as f:
    json.dump(artist_map, f, indent = 2)
#
print("Writing work map to json")
with open("work_map.json", "w") as f:
    json.dump(work_map, f, indent = 2)

# pprint(counts)
# pprint(counts_rock)
# print(index)
# print("escrevendo artistas")
with open("artists.json", "w") as f:
    json.dump(filtered, f)
print("escrevendo artistas só três featuress")
with open("features_artists.json", "w") as f:
    json.dump(filtered_only_features, f, indent = 2)
print("escrevendo artistas de rock")
with open("rock_artists.json", "w") as f:
    json.dump(filtered_rock, f)
print("escrevendo counts")
with open("counts.json", "w") as f:
    json.dump(counts, f, indent = 2)
print("escrevendo counts de rock")
with open("rock_counts.json", "w") as f:
    json.dump(counts_rock, f, indent = 2)


