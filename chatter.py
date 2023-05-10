#!/usr/bin/env python

import telebot
import asyncio
import openai
import settings
import os
import textract
import sqlite3
from pydub import AudioSegment

bot = telebot.TeleBot(settings.telebot_key)
openai.api_key = settings.openai_key

script_path = os.path.abspath(__file__)

# Get the directory containing the current script
script_dir = os.path.dirname(script_path)


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
