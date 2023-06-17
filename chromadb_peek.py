#!/usr/bin/env python
import chromadb
from chromadb.config import Settings
from pprint import pprint as pp
import sys

collection_name = sys.argv[1]
print("Collection name:",collection_name)
persist_directory = "chromadb"
chroma_client = chromadb.Client(Settings(persist_directory=persist_directory,chroma_db_impl="duckdb+parquet",))
collection = chroma_client.get_or_create_collection(name=collection_name)


print('KB presently has %s entries' % collection.count())
print('\n\nBelow are the top 10 entries:')
results = collection.peek()
pp(results)
