#!/usr/bin/env python

import telebot
from openai import OpenAI
import settings
import os
import textract
import pprint
import base64
# import chromadb
# import threading
# import tiktoken
# from re import template
# from urlextract import URLExtract
# import urllib
# from chromadb.config import Settings
import time
from uuid import uuid4
import sqlite3
from datetime import datetime, timedelta
import yahooquery as yq
import numpy as np
from numerize import numerize
from sklearn.cluster import KMeans
from pydub import AudioSegment

bot = telebot.TeleBot(settings.telebot_key)
# openai.api_key = settings.openai_key

script_path = os.path.abspath(__file__)

# Get the directory containing the current script
script_dir = os.path.dirname(script_path)

bot.send_message(6139828455,"Hello")
