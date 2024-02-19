#!/usr/bin/env python 
import telebot 
import settings 
import os
import sys
import sqlite3
import datetime
import urllib.parse
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
            results = pd.read_csv(os.path.join(script_dir,'small_results.csv'))
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a>"
            results['pptext'] = "Top 5 latest news for '" + results['desc'] + "' (Ticker: " + results['ticker'] + ") in this week. Please sort by date descending and format your answers with <date of news> - <source of news> - <news summary>"
            results['ppurl'] = results['pptext'].apply(urllib.parse.quote)
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a> - <a href='https://clockin.cbmyportal.org/view/portal/echo?q=" + results['ppurl'] + "'>PP</a>"

            results['gapdiff'] = results['price'] - results['gap']
            results = results.loc[results['First Green']==1]
            results = results.loc[results['Volume 10 Times Above Yesterday Average']==1]
            results = results.loc[results['price']>0.2]
            results = results.sort_values(by=['gapdiff'],ascending=True)
            tosend = results.iloc[:20]
            tosend = tosend[['ticker','gapdiff']]
            tosend = tosend.set_index('ticker')
            print(tabulate(tosend,headers="keys"))
            bot.send_message(subscriber[1],'Small Caps Gap Diff\n\n' + tabulate(tosend,headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
