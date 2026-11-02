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

# Remove various artists, [unknown] e [no artist]
clear_dull_artists_query = """
MATCH (a:Artist)
WHERE a.id IN ["89ad4ac3-39f7-470e-963a-56509c546377", "125ec42a-7229-4250-afc5-e057484327fe", "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61"]
DETACH DELETE a
"""

# ==========================================
# 3. EXECUÇÃO
# ==========================================

driver.execute_query(clear_dull_artists_query)

print("Limpeza da base do Neo4j realizada com sucesso!")
