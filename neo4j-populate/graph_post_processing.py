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

# ==========================================
# 2. DEFINIÇÃO DE QUERIES
# ==========================================

# Remove Special Purpose Artists
clear_dull_artists_query = """
MATCH (a:Artist)
WHERE a.id IN ["f731ccc4-e22a-43af-a747-64213329e088", // [anonymous]
               "33cf029c-63b0-41a0-9855-be2a3665fb3b", // [data]
               "314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc", // [dialogue]
               "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61", // [no artist]
               "9be7f096-97ec-4615-8957-8d40b5dcbc41", // [traditional]
               "125ec42a-7229-4250-afc5-e057484327fe", // [unknown]
               "89ad4ac3-39f7-470e-963a-56509c546377", // Various Artists
               "7e84f845-ac16-41fe-9ff8-df12eb32af55", // MusicBrainz Test Artist
               "66ea0139-149f-4a0c-8fbf-5ea9ec4a6e49", // [Disney]
               "a0ef7e1d-44ff-4039-9435-7d5fefdeecc9", // [theatre]
               "90068d37-bae7-4292-be4a-704c145bd616", // [church chimes]
               "80a8851f-444c-4539-892b-ad2a49292aa9"  // [language instruction]
               ]
DETACH DELETE a
"""

# ==========================================
# 3. EXECUÇÃO
# ==========================================

driver.execute_query(clear_dull_artists_query)

print("Limpeza da base do Neo4j realizada com sucesso!")
