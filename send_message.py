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
            results = pd.read_csv(os.path.join(script_dir,'results_profitability.csv'))
            results = results[results['Late Start']==0]
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"

            curcount = {}
            results.sort_values(by=['prev_marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            results.sort_values(by=['opening_marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            results.sort_values(by=['late_marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            results.sort_values(by=['hour_marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            results.sort_values(by=['daily_marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            results.sort_values(by=['marks'],ascending=False,inplace=True)
            for ct in results.iloc[:10].values:
                cticker = ct[1]
                if cticker in curcount:
                    curcount[cticker] += 1
                else:
                    curcount[cticker] = 1
            sortedcount = sorted(curcount.items(), key=lambda x:x[1], reverse=True)
            bot.send_message(subscriber[1],'Recurring Tickers For ' + results['date'].max() + '\n\n' + tabulate(sortedcount,headers=['Ticker','Count']),parse_mode='HTML') #,tablefmt="grid"))

            results.sort_values(by=['marks'],ascending=False,inplace=True)
            tosend = results[['ticker','marks','price']].set_index('ticker')
            bot.send_message(subscriber[1],'Marks\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            results.sort_values(by=['late_marks'],ascending=False,inplace=True)
            tosend = results[['ticker','late_marks','price']].set_index('ticker')
            bot.send_message(subscriber[1],'Late Marks\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            beware = 'Beware of these props:\n'
            beware += 'Yesterday Loss: ' + str(results['Perc Yesterday Loss'].max()) + '\n'
            beware += 'Sluggish Ticker: ' + str(results['Perc Sluggish Ticker'].max()) + '\n'
            beware += 'Lower High: ' + str(results['Perc Lower High'].max()) + '\n'
            bot.send_message(subscriber[1],beware,parse_mode='HTML') #,tablefmt="grid"))

            perc_prop = []
            for col in results.columns:
                if col[0:5] == 'Perc ':
                    perc_prop.append(col)
            max_prop = []
            for col in perc_prop:
                cperf = {'Prop':col,'Perc':results[col].max()}
                max_prop.append(cperf)
            max_prop.sort(key=lambda x: x['Perc'], reverse=True)
            bot.send_message(subscriber[1],'Top Props:\n\n' + tabulate(max_prop[:20],headers='keys'),parse_mode='HTML')
