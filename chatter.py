#!/usr/bin/env python

import telebot
import asyncio
import openai
import settings
import math
import os
import textract
import chromadb
import threading
from chromadb.config import Settings
import time
from uuid import uuid4
import threading
from datetime import datetime, timedelta
import yahooquery as yq
import numpy as np
import pandas as pd
from numerize import numerize
from sklearn.cluster import KMeans
import sqlite3
from pydub import AudioSegment

bot = telebot.TeleBot(settings.telebot_key)
openai.api_key = settings.openai_key

script_path = os.path.abspath(__file__)

# Get the directory containing the current script
script_dir = os.path.dirname(script_path)

sentinal = None
stop_sentinal = False
watched_tickers = []

# messages = []

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

default_system_text = 'system_reflective_journaling.txt'
conversation = list()
# conversation.append({'role': 'system', 'content': open_file('system_default.txt')})
conversation.append({'role': 'system', 'content': open_file(default_system_text)})
user_messages = list()
all_messages = list()



def chatbot(messages, model="gpt-4", temperature=0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']
            
            ###    trim message object
            if response['usage']['total_tokens'] >= 7000:
                a = messages.pop(1)
            
            return text
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                a = messages.pop(1)
                print('\n\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\n\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            time.sleep(2 ** (retry - 1) * 5)

def get_response(message,content):

    tic = time.perf_counter()
    persist_directory = "chromadb"
    chroma_client = chromadb.Client(Settings(persist_directory=persist_directory,chroma_db_impl="duckdb+parquet",))
    collection = chroma_client.get_or_create_collection(name="knowledge_base")
    toc = time.perf_counter()
    print(f"Setup chroma in {toc - tic:0.4f} seconds")
    print("\n\nKB Collection Amount:",collection.count())

    text = content
    user_messages.append(text)
    all_messages.append('USER: %s' % text)
    conversation.append({'role': 'user', 'content': text})

    if len(all_messages) > 5:
        all_messages.pop(0)
    main_scratchpad = '\n\n'.join(all_messages).strip()

    current_profile = open_file('user_profile.txt')
    kb = 'No KB articles yet'
    if collection.count() > 0:
        tic = time.perf_counter()
        results = collection.query(query_texts=[content], n_results=1)
        kb = results['documents'][0][0]
        print('\n\nDEBUG: Found results %s' % results)
        toc = time.perf_counter()
        print(f"Chroma query in {toc - tic:0.4f} seconds")
    # default_system = open_file('system_default.txt').replace('<<PROFILE>>', current_profile).replace('<<KB>>', kb)
    tic = time.perf_counter()
    default_system = open_file(default_system_text).replace('<<KB>>', kb)
    print('SYSTEM: %s' % default_system)
    conversation[0]['content'] = default_system
    print("\n==============================================================================================================\n")

    response = chatbot(conversation)
    toc = time.perf_counter()
    print(f"Got response in {toc - tic:0.4f} seconds")
    conversation.append({'role': 'assistant', 'content': response})
    all_messages.append('CHATBOT: %s' % response)
    print('\n\nCHATBOT: %s' % response)
    print("\n==============================================================================================================\n")

    # try:
    #
    #     if len(user_messages) > 3:
    #         user_messages.pop(0)
    #     user_scratchpad = '\n'.join(user_messages).strip()
    #
    #     print('\n\nUpdating user profile...')
    #     profile_length = len(current_profile.split(' '))
    #     profile_conversation = list()
    #     profile_conversation.append({'role': 'system', 'content': open_file('system_update_user_profile.txt').replace('<<UPD>>', current_profile).replace('<<WORDS>>', str(profile_length))})
    #     profile_conversation.append({'role': 'user', 'content': user_scratchpad})
    #     profile = chatbot(profile_conversation)
    #     save_file('user_profile.txt', profile)
    #     print(profile)
    #     print("\n==============================================================================================================\n")
    # except Exception as oops:
    #     print("Caught error updating user profile: ",oops)

    try:

        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()

        print('\n\nUpdating KB...')
        print(main_scratchpad)
        print("\n==============================================================================================================\n")
        if collection.count() == 0:
            # yay first KB!
            tic = time.perf_counter()
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('system_instantiate_new_kb.txt')})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            new_id = str(uuid4())
            collection.add(documents=[article],ids=[new_id])
            toc = time.perf_counter()
            print(f"Chroma added in {toc - tic:0.4f} seconds")
        else:
            tic = time.perf_counter()
            results = collection.query(query_texts=[content], n_results=1)
            toc = time.perf_counter()
            print(f"Chroma done query in {toc - tic:0.4f} seconds")
            kb = results['documents'][0][0]
            kb_id = results['ids'][0][0]
            
            # Expand current KB
            tic = time.perf_counter()
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('system_update_existing_kb.txt').replace('<<KB>>', kb)})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
            toc = time.perf_counter()
            print(f"Preparing kb in {toc - tic:0.4f} seconds")
            tic = time.perf_counter()
            print("\n\nKB Convo:\n")
            print(kb_convo)
            print("\nArticle:\n")
            print(article)
            print("\n==============================================================================================================\n")
            collection.update(ids=[kb_id],documents=[article])
            toc = time.perf_counter()
            print(f"Chroma done update in {toc - tic:0.4f} seconds")
            
            # Split KB if too large
            kb_len = len(article.split(' '))
            if kb_len > 1000:
                print("KB article too big. Splitting in two")
                tic = time.perf_counter()
                kb_convo = list()
                kb_convo.append({'role': 'system', 'content': open_file('system_split_kb.txt')})
                kb_convo.append({'role': 'user', 'content': article})
                articles = chatbot(kb_convo).split('ARTICLE 2:')
                a1 = articles[0].replace('ARTICLE 1:', '').strip()
                a2 = articles[1].strip()
                collection.update(ids=[kb_id],documents=[a1])
                toc = time.perf_counter()
                print(f"Chroma updated in {toc - tic:0.4f} seconds")
                tic = time.perf_counter()
                new_id = str(uuid4())
                collection.add(documents=[a2],ids=[new_id])
                toc = time.perf_counter()
                print(f"Chroma other half added in {toc - tic:0.4f} seconds")
    except Exception as oops:
        print("Caught error updating KB:",oops)
    
    try:
        tic = time.perf_counter()
        chroma_client.persist()
        toc = time.perf_counter()
        print(f"Chroma done persist in {toc - tic:0.4f} seconds")
    except Exception as oops:
        print("Caught error persisting Chromadb:",oops)

    return response

    # try:
    #     con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
    #     cursor = con.cursor()
    #     cursor.execute("INSERT INTO chat (timestamp, role, user, chat, message) VALUES (datetime('now'), 'user', ?, ?, ?)", (message.from_user.id, message.chat.id, content))
    #     con.commit()
    #     messages = cursor.execute("SELECT message,role FROM chat WHERE chat = ? ORDER BY timestamp", (message.chat.id,)).fetchall()
    #     history = [{'role':'assistant','content':m[0]} if m[1]=='assistant' else {'role':'user','content':m[0]} for m in messages]
    #
    #     # messages.append({'role':'user','content':content})
    #     response = openai.ChatCompletion.create(
    #         model='gpt-4',
    #         messages=history
    #     )
    #     cursor.execute("INSERT INTO chat (timestamp, role, user, chat, message) VALUES (datetime('now'), 'assistant', ?, ?, ?)", (message.from_user.id, message.chat.id, response.choices[0].message.content))
    #     con.commit()
    #     cursor.close()
    #     # messages.append(response.choices[0].message)
    #     return response.choices[0].message.content
    # except Exception as e:
    #     raise

@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        # con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
        # cursor = con.cursor()
        # cursor.execute("delete from chat where user=? and chat=?", (message.from_user.id, message.chat.id))
        # con.commit()
        # cursor.close()
        conversation.clear()
# conversation.append({'role': 'system', 'content': open_file('system_default.txt')})
        conversation.append({'role': 'system', 'content': open_file(default_system_text)})
        user_messages.clear()
        all_messages.clear()
        response = get_response(message,'Hello. My name is ' + message.from_user.first_name)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['length','size'])
def msg_length(message):
    try:
        # con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
        # cursor = con.cursor()
        # messages = cursor.execute("SELECT message,role FROM chat WHERE chat = ? ORDER BY timestamp", (message.chat.id,)).fetchall()
        response = 'Message length: ' + str(len(all_messages)) + ' messages.'
        # con.commit()
        # cursor.close()
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['setup','start'])
def setup(message):
    try:
        response = get_response(message,'Hello. My name is ' + message.from_user.first_name)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['stock','ticker'])
def stock(message):
    try:
        tokens = message.text.split(' ')
        ticker = tokens[1].upper()
        yqticker = yq.Ticker(ticker)
        end_date = datetime.now()
        days = 120
        start_date = end_date - timedelta(days=days)
        candles = yqticker.history(start=start_date,end=end_date,interval='1d')
        
        response = get_response(message,"Ticker " + ticker + " candles: " + str(candles))
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

def watch_stock_thread(message):
    global stop_sentinal, watched_tickers
    tokens = message.text.split(' ')
    ticker = tokens[1].upper()
    if ticker in watched_tickers:
        bot.reply_to(message, "Already watching " + ticker)
    else:
        watched_tickers.append(ticker)
        bot.reply_to(message, "Watching " + ticker)
    while not stop_sentinal:
        # yqticker = yq.Ticker(ticker)
        for tick in watched_tickers:
            # bot.reply_to(message, "Ticker " + tick + " price: ")
            print("Ticker " + tick + " price: ")
        time.sleep(10)

@bot.message_handler(commands=['watch'])
def watch_stock(message):
    try:
        global sentinal, stop_sentinal, watched_tickers
        tokens = message.text.split(' ')
        if sentinal is None:
            stop_sentinal = False
            sentinal = threading.Thread(target=watch_stock_thread, args=(message,))
            sentinal.start()
            bot.reply_to(message, "Sentinal started watching")
        else:
            if len(tokens) > 1 and tokens[1].upper()!='STOP':
                watch_stock_thread(message)
            else:
                stop_sentinal = True
                #sentinal.join()
                sentinal = None
                watched_tickers = []
                bot.reply_to(message, "Sentinal stopped watching")
    except Exception as e:
        print("Error: ",str(e))

@bot.message_handler(commands=['levels'])
def stock_levels(message):
    #try:
        tokens = message.text.split(' ')
        ticker = tokens[1].upper()
        yqticker = yq.Ticker(ticker)
        end_date = datetime.now()
        days = 200
        start_date = end_date - timedelta(days=days)
        candles = yqticker.history(start=start_date,end=end_date,interval='1d')
        minute_start_date = end_date - timedelta(days=1)
        minute_candles = yqticker.history(start=minute_start_date,end=end_date,interval='5m')

        response = "Levels:"
        min = candles['low'].min()
        max = candles['high'].max()
        p_range = candles['high'] - candles['low']
        range_avg = p_range.mean()
        vol_avg = candles['volume'].mean()
        min_vol_avg = minute_candles['volume'].mean()
        response += "\nStart: " + str(start_date)
        response += "\nEnd: " + str(end_date)
        response += "\nMin: " + str(min)
        response += "\nMax: " + str(max)
        response += "\nRange Avg: " + str(numerize.numerize(range_avg))
        response += "\nVol Avg: " + str(numerize.numerize(vol_avg))
        if min_vol_avg!=None and not np.isnan(min_vol_avg) and int(min_vol_avg)>100:
            response += "\n5 Min Vol Avg: " + str(numerize.numerize(min_vol_avg))

        datarange = max - min
        if datarange < 50:
            kint = int(datarange / 0.5)
        else:
            kint = int(datarange % 20)

        datalen = len(candles)

        highlevels = np.array(candles['high'])
        kmeans = KMeans(n_clusters=kint).fit(highlevels.reshape(-1,1))
        highclusters = kmeans.predict(highlevels.reshape(-1,1))

        resistancelevels = {}

        for cidx in range(datalen):
            curcluster = highclusters[cidx]
            if curcluster not in resistancelevels:
                resistancelevels[curcluster] = 1
            else:
                resistancelevels[curcluster] += 1

        donecluster = []
        finalreslevels = {}
        dresponse = ""
        for cidx in range(datalen):
            candle = candles.iloc[cidx]
            curcluster = highclusters[cidx]
            if resistancelevels[curcluster] > 2:
                if curcluster not in donecluster:
                    donecluster.append(curcluster)
                    finalreslevels[curcluster] = {'level':candle['high'],'count':1}
                else:
                    finalreslevels[curcluster] = {'level':(finalreslevels[curcluster]['level'] + candle['high'])/2,'count':finalreslevels[curcluster]['count']+1}

        response += "\n\nResistance levels:"
        for lvl,clstr in sorted(finalreslevels.items(),key=lambda x: x[1]['level']):
            response += "\n" + str(clstr['level']) + " : " + str(clstr['count'])

        if datarange < 50:
            kint = int(datarange / 0.5)
        else:
            kint = int(datarange % 20)
        lowlevels = np.array(candles['low'])
        kmeans = KMeans(n_clusters=kint).fit(lowlevels.reshape(-1,1))
        lowclusters = kmeans.predict(lowlevels.reshape(-1,1))

        supportlevels = {}

        for cidx in range(datalen):
            curcluster = lowclusters[cidx]
            if curcluster not in supportlevels:
                supportlevels[curcluster] = 1
            else:
                supportlevels[curcluster] += 1

        donecluster = []
        finalsuplevels = {}
        dresponse = ""
        for cidx in range(datalen):
            candle = candles.iloc[cidx]
            curcluster = lowclusters[cidx]
            if supportlevels[curcluster] > 2:
                if curcluster not in donecluster:
                    donecluster.append(curcluster)
                    finalsuplevels[curcluster] = {'level':candle['low'],'count':1}
                else:
                    finalsuplevels[curcluster] = {'level':(finalsuplevels[curcluster]['level'] + candle['low'])/2,'count':finalsuplevels[curcluster]['count']+1}

        response += "\n\nSupport levels:"
        for lvl,clstr in sorted(finalsuplevels.items(),key=lambda x: x[1]['level']):
            response += "\n" + str(clstr['level']) + " : " + str(clstr['count'])
        
        response += "\n\n" + dresponse
        bot.reply_to(message, response)
    #except Exception as e:
        #bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['imagine'])
def imagine(message):
    print("Got image request:",message)
    try:
        response = openai.Image.create(
            prompt=message.text,
        n=1,
        size="1024x1024"
        )
        image_url = response['data'][0]['url']
        bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(content_types=['document'])
def document_processing(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(os.path.join(script_dir,file_info.file_path), 'wb') as new_file:
            new_file.write(downloaded_file)
        filetext = textract.process(os.path.join(script_dir,file_info.file_path))
        usermsg = str(message.caption) + "\nFile contents: " + str(filetext).replace('\n\n','\n')
        response = get_response(message,usermsg)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        filename = 'voice_' + str(message.from_user.id)
        with open(os.path.join(script_dir,'voices',filename + '.ogg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        ogg_audio = AudioSegment.from_file(os.path.join(script_dir,'voices',filename + '.ogg'), format="ogg")
        ogg_audio.export(os.path.join(script_dir,'voices',filename + '.mp3'), format="mp3")
        transcript = openai.Audio.transcribe("whisper-1", open(os.path.join(script_dir,'voices',filename + '.mp3'),'rb'))
        response = get_response(message,transcript.text)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler()
def catch_all(message):
    if message.chat.type == 'private' or message.entities!=None:
        try:
            response = get_response(message,message.text)
            bot.reply_to(message, response)
        except Exception as e:
            bot.reply_to(message, "Sorry, " + str(e))
    else:
        pass


# update_db()
# tostart = []
# tostart.append({'role':'system','content':'You are abdza_chatter_bot. A helpful and kind bot.'})
# response = openai.ChatCompletion.create(
#     model='gpt-4',
#     messages=tostart
# )

bot.infinity_polling(timeout=60,long_polling_timeout=60)
