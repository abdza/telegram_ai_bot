#!/usr/bin/env python

import telebot
import asyncio
import openai
import settings
import math
import os
import textract
import time
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

def update_db():
    con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
    cursor = con.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY, timestamp, role TEXT, user TEXT, chat TEXT, message TEXT)")
    con.commit()
    cursor.close()

def get_response(message,content):
    try:
        con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
        cursor = con.cursor()
        cursor.execute("INSERT INTO chat (timestamp, role, user, chat, message) VALUES (datetime('now'), 'user', ?, ?, ?)", (message.from_user.id, message.chat.id, content))
        con.commit()
        messages = cursor.execute("SELECT message,role FROM chat WHERE chat = ? ORDER BY timestamp", (message.chat.id,)).fetchall()
        history = [{'role':'assistant','content':m[0]} if m[1]=='assistant' else {'role':'user','content':m[0]} for m in messages]

        # messages.append({'role':'user','content':content})
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=history
        )
        cursor.execute("INSERT INTO chat (timestamp, role, user, chat, message) VALUES (datetime('now'), 'assistant', ?, ?, ?)", (message.from_user.id, message.chat.id, response.choices[0].message.content))
        con.commit()
        cursor.close()
        # messages.append(response.choices[0].message)
        return response.choices[0].message.content
    except Exception as e:
        raise

@bot.message_handler(commands=['reset'])
def reset(message):
    try:
        con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
        cursor = con.cursor()
        cursor.execute("delete from chat where user=? and chat=?", (message.from_user.id, message.chat.id))
        con.commit()
        cursor.close()
        response = get_response(message,'Hello. My name is ' + message.from_user.first_name)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['length','size'])
def msg_length(message):
    try:
        con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
        cursor = con.cursor()
        messages = cursor.execute("SELECT message,role FROM chat WHERE chat = ? ORDER BY timestamp", (message.chat.id,)).fetchall()
        response = 'Message length: ' + str(len(messages)) + ' messages.'
        con.commit()
        cursor.close()
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
    try:
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
        vol_avg = candles['volume'].mean()
        min_vol_avg = minute_candles['volume'].mean()
        response += "\nStart: " + str(start_date)
        response += "\nEnd: " + str(end_date)
        response += "\nMin: " + str(min)
        response += "\nMax: " + str(max)
        response += "\nVol Avg: " + str(numerize.numerize(vol_avg))
        response += "\n5 Min Vol Avg: " + str(numerize.numerize(min_vol_avg))

        datarange = max - min
        kint = int(datarange / 0.5)

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

        kint = int(datalen/10)
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
    except Exception as e:
        bot.reply_to(message, "Sorry, " + str(e))

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


update_db()
tostart = []
tostart.append({'role':'system','content':'You are abdza_chatter_bot. A helpful and kind bot.'})
response = openai.ChatCompletion.create(
    model='gpt-4',
    messages=tostart
)

bot.infinity_polling()
