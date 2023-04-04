#!/usr/bin/env python

import telebot
import openai
import settings

bot = telebot.TeleBot(settings.telebot_key)
openai.api_key = settings.openai_key

messages = []

@bot.message_handler(commands=['setup'])
def setup(message):
    messages.append({'role':'user','content':'My name is ' + message.from_user.first_name})

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
