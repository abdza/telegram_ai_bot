#!/usr/bin/env python

import telebot
import openai
import settings
import os
from pydub import AudioSegment

bot = telebot.TeleBot(settings.telebot_key)
openai.api_key = settings.openai_key

script_path = os.path.abspath(__file__)

# Get the directory containing the current script
script_dir = os.path.dirname(script_path)

messages = []

@bot.message_handler(commands=['setup','start'])
def setup(message):
    messages.append({'role':'user','content':'Hello. My name is ' + message.from_user.first_name})
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )
    messages.append(response.choices[0].message)
    bot.reply_to(message, response.choices[0].message.content)

@bot.message_handler(commands=['imagine'])
def imagine(message):
    response = openai.Image.create(
        prompt=message.text,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    bot.send_photo(message.chat.id, image_url)

@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = 'voice_' + str(message.from_user.id)
    with open(os.path.join(script_dir,'voices',filename + '.ogg'), 'wb') as new_file:
        new_file.write(downloaded_file)
    ogg_audio = AudioSegment.from_file(os.path.join(script_dir,'voices',filename + '.ogg'), format="ogg")
    ogg_audio.export(os.path.join(script_dir,'voices',filename + '.mp3'), format="mp3")
    transcript = openai.Audio.transcribe("whisper-1", open(os.path.join(script_dir,'voices',filename + '.mp3'),'rb'))
    messages.append({'role':'user','content':transcript.text})
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )
    messages.append(response.choices[0].message)
    bot.reply_to(message, response.choices[0].message.content)

@bot.message_handler()
def catch_all(message):
    messages.append({'role':'user','content':message.text})
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )
    messages.append(response.choices[0].message)
    bot.reply_to(message, response.choices[0].message.content)

bot.infinity_polling()
