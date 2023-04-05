#!/usr/bin/env python

from telebot.async_telebot import AsyncTeleBot
import asyncio
import openai
import settings
import os
import textract
from pydub import AudioSegment

bot = AsyncTeleBot(settings.telebot_key)
openai.api_key = settings.openai_key

script_path = os.path.abspath(__file__)

# Get the directory containing the current script
script_dir = os.path.dirname(script_path)

messages = []

def get_response(content):
    try:
        messages.append({'role':'user','content':content})
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages
        )
        messages.append(response.choices[0].message)
        return response.choices[0].message.content
    except Exception as e:
        raise

@bot.message_handler(commands=['reset'])
async def reset(message):
    try:
        messages.clear()
        response = get_response('Hello. My name is ' + message.from_user.first_name)
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['length','size'])
async def msg_length(message):
    try:
        response = 'Message length: ' + str(len(messages)) + ' messages.'
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['setup','start'])
async def setup(message):
    try:
        response = get_response('Hello. My name is ' + message.from_user.first_name)
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(commands=['imagine'])
async def imagine(message):
    try:
        response = openai.Image.create(
            prompt=message.text,
        n=1,
        size="1024x1024"
        )
        image_url = response['data'][0]['url']
        await bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(content_types=['document'])
async def document_processing(message):
    try:
        file_info = await asyncio.wait_for(bot.get_file(message.document.file_id),timeout=60)
        downloaded_file = await asyncio.wait_for(bot.download_file(file_info.file_path),timeout=60)
        with open(os.path.join(script_dir,file_info.file_path), 'wb') as new_file:
            new_file.write(downloaded_file)
        filetext = textract.process(os.path.join(script_dir,file_info.file_path))
        usermsg = str(message.caption) + "\nFile contents: " + str(filetext).replace('\n\n','\n')
        response = get_response(usermsg)
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler(content_types=['voice'])
async def voice_processing(message):
    try:
        file_info = await asyncio.wait_for(bot.get_file(message.voice.file_id),timeout=60)
        downloaded_file = await asyncio.wait_for(bot.download_file(file_info.file_path),timeout=60)
        filename = 'voice_' + str(message.from_user.id)
        with open(os.path.join(script_dir,'voices',filename + '.ogg'), 'wb') as new_file:
            new_file.write(downloaded_file)
        ogg_audio = AudioSegment.from_file(os.path.join(script_dir,'voices',filename + '.ogg'), format="ogg")
        ogg_audio.export(os.path.join(script_dir,'voices',filename + '.mp3'), format="mp3")
        transcript = openai.Audio.transcribe("whisper-1", open(os.path.join(script_dir,'voices',filename + '.mp3'),'rb'))
        response = get_response(transcript.text)
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

@bot.message_handler()
async def catch_all(message):
    try:
        response = get_response(message.text)
        await bot.reply_to(message, response)
    except Exception as e:
        await bot.reply_to(message, "Sorry, " + str(e))

asyncio.run(bot.polling())
