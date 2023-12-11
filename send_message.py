#!/usr/bin/env python 
import telebot 
import settings 
import os
import sys
import sqlite3
import pandas as pd
from tabulate import tabulate

bot = telebot.TeleBot(settings.telebot_key)

script_path = os.path.abspath(__file__)

script_dir = os.path.dirname(script_path)

con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
cursor = con.cursor()
thread = cursor.execute("SELECT * FROM threads ORDER BY timestamp desc limit 1").fetchall()
user_id = thread[0][3]
print("thread:",user_id)
if len(sys.argv)>1:
    toout = sys.argv[1].encode('utf-8').decode('unicode_escape')
    bot.send_message(user_id,toout)
else:
    results = pd.read_csv(os.path.join(script_dir,'results_predicted.csv')).set_index("date")
    results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
    tosend = results[['ticker','predicted_profitable']]
    bot.send_message(user_id,tabulate(tosend,headers="keys",tablefmt="github"),parse_mode='HTML')

    results = pd.read_csv(os.path.join(script_dir,'results.csv')).set_index("date")
    results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
    results.sort_values(by=['marks'],ascending=False,inplace=True)
    tosend = results[['ticker','marks','price']]
    bot.send_message(user_id,tabulate(tosend.iloc[:10],headers="keys",tablefmt="github"),parse_mode='HTML')
