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
subscribers = cursor.execute("SELECT * FROM subscribers where service=?",("STOCK",)).fetchall()
if len(subscribers)>0:
    for subscriber in subscribers:
        print("thread:",subscriber[1])
        if len(sys.argv)>1:
            toout = sys.argv[1].encode('utf-8').decode('unicode_escape')
            bot.send_message(subscriber[1],toout)
        else:
            results = pd.read_csv('results_profitability.csv')
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            results.sort_values(by=['predicted_profitable'],ascending=False,inplace=True)
            print("Results:",tabulate(results.iloc[:10],headers="keys",tablefmt="grid"))
            tosend = results[['ticker','predicted_profitable','price']]
            bot.send_message(subscriber[1],tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            results.sort_values(by=['marks'],ascending=False,inplace=True)
            print("Mark Results:",tabulate(results.iloc[:10],headers="keys",tablefmt="grid"))
            tosend = results[['ticker','marks','price']]
            bot.send_message(subscriber[1],tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            yesterday = results[results['Yesterday Profitable']==1]
            yesterday = yesterday[yesterday['2 Days Ago Profitable']==1]
            yesterday.sort_values(by=['price'],inplace=True)
            print("Yesterday Profitable:",tabulate(yesterday.iloc[:10],headers="keys",tablefmt="grid"))
            tosend = yesterday[['ticker','marks','price']]
            bot.send_message(subscriber[1],tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            yesterday = results[results['Yesterday Profitable']==1]
            yesterday = yesterday[yesterday['2 Days Ago Profitable']==0]
            yesterday.sort_values(by=['price'],inplace=True)
            print("Yesterday Profitable:",tabulate(yesterday.iloc[:10],headers="keys",tablefmt="grid"))
            tosend = yesterday[['ticker','marks','price']]
            bot.send_message(subscriber[1],tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
