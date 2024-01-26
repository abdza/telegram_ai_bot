#!/usr/bin/env python 
import telebot 
import settings 
import os
import sys
import sqlite3
import datetime
import pandas as pd
from tabulate import tabulate

bot = telebot.TeleBot(settings.telebot_key)

script_path = os.path.abspath(__file__)

script_dir = os.path.dirname(script_path)

con = sqlite3.connect(os.path.join(script_dir,'chatter.db'))
cursor = con.cursor()
subscribers = cursor.execute("SELECT * FROM subscribers where service=?",("STOCK",)).fetchall()
if len(subscribers)>0:
    for subscriber in subscribers:
        print("thread:",subscriber[1])
        if len(sys.argv)>1:
            toout = sys.argv[1].encode('utf-8').decode('unicode_escape')
            bot.send_message(subscriber[1],toout)
        else:
            results = pd.read_csv(os.path.join(script_dir,'hour_pattern.csv'))
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"

            tosend = results.loc[results['type']=='double']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible hour double bottom\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='up']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible hour up channel\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='nova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible hour super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='recentnova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Recent hour super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='volumenova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible hour volume super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            results = pd.read_csv(os.path.join(script_dir,'raw_data.csv'))
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            results = results.sort_values(by=['range'],ascending=False)
            tosend = results.iloc[:20]
            tosend = tosend[['ticker','range','date']]
            tosend = tosend.set_index('ticker')
            bot.send_message(subscriber[1],'Hour Pass High Range\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
