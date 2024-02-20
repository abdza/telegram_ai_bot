#!/usr/bin/env python 
import telebot 
import settings 
import os
import sys
import urllib.parse
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
            results = pd.read_csv(os.path.join(script_dir,'pattern.csv'))
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a>"
            results['pptext'] = "Top 5 latest news for '" + results['desc'] + "' (Ticker: " + results['ticker'] + ") in this week. Please sort by date descending and format your answers with <date of news> - <source of news> - <news summary>"
            results['ppurl'] = results['pptext'].apply(urllib.parse.quote)
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a> - <a href='https://clockin.cbmyportal.org/view/portal/echo?q=" + results['ppurl'] + "'>PP</a>"
            results = results.drop(columns=['pptext','ppurl'])

            tosend = results.loc[results['type']=='hns']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible head and shoulders\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='double']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible double bottom\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='up']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible up channel\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='down']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible down channel\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='nova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='recentnova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Recent super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            tosend = results.loc[results['type']=='volumenova']
            tosend.set_index('ticker',inplace=True)
            tosend = tosend.drop(columns=['type',])
            bot.send_message(subscriber[1],'Possible volume super nova\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            results = pd.read_csv(os.path.join(script_dir,'raw_data.csv'))
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a>"
            results['pptext'] = "Top 5 latest news for '" + results['desc'] + "' (Ticker: " + results['ticker'] + ") in this week. Please sort by date descending and format your answers with <date of news> - <source of news> - <news summary>"
            results['ppurl'] = results['pptext'].apply(urllib.parse.quote)
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a> - <a href='https://clockin.cbmyportal.org/view/portal/echo?q=" + results['ppurl'] + "'>PP</a>"
            results = results.drop(columns=['pptext','ppurl'])
            results = results.sort_values(by=['range'],ascending=False)
            tosend = results.iloc[:20]
            tosend = tosend[['ticker','range','date']]
            tosend = tosend.set_index('ticker')
            bot.send_message(subscriber[1],'Pass High Range\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
