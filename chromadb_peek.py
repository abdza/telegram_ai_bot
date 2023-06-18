#!/usr/bin/env python
import chromadb
from chromadb.config import Settings
from pprint import pprint as pp
import sys
import os

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
chromadb_dir = os.path.join(script_dir,'chromadb')

collection_name = sys.argv[1]
print("Collection name:",collection_name)
chroma_client = chromadb.Client(Settings(persist_directory=chromadb_dir,chroma_db_impl="duckdb+parquet",))
collection = chroma_client.get_or_create_collection(name=collection_name)


print('KB presently has %s entries' % collection.count())
print('\n\nBelow are the top 10 entries:')
results = collection.peek()
pp(results)
