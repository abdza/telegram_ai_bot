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
            results = pd.read_csv(os.path.join(script_dir,'results.csv'))
            results = results[results['Late Start']==0]
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a>"
            # results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a>"
            results['pptext'] = "Top 5 latest news for '" + results['desc'] + "' (Ticker: " + results['ticker'] + ") in this week. Please sort by date descending and format your answers with <date of news> - <source of news> - <news summary>"
            results['ppurl'] = results['pptext'].apply(urllib.parse.quote)
            results['ticker'] = "<a href='https://tradingview.com/chart?symbol=" + results['ticker'] + "'>" + results['ticker'] + "</a> - <a href='https://finviz.com/quote.ashx?t=" + results['ticker'] + "&p=d'>FZ</a> - <a href='https://clockin.cbmyportal.org/view/portal/echo?q=" + results['ppurl'] + "'>PP</a>"
            results = results.drop(columns=['ppurl','pptext'])

            winlimit = 20
            curcount = {}
            # results.sort_values(by=['prev_marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'p'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'p'
            # results.sort_values(by=['opening_marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'o'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'o'
            # results.sort_values(by=['late_marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'l'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'l'
            # results.sort_values(by=['hour_marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'h'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'h'
            # results.sort_values(by=['daily_marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'd'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'd'
            # results.sort_values(by=['marks'],ascending=False,inplace=True)
            # for ct in results.iloc[:winlimit].values:
            #     cticker = ct[1]
            #     if cticker in curcount:
            #         curcount[cticker]['count'] += 1
            #         curcount[cticker]['marker'] += 'm'
            #     else:
            #         curcount[cticker] = {}
            #         curcount[cticker]['count'] = 1
            #         curcount[cticker]['marker'] = 'm'
            # sortedcount = sorted(curcount.items(), key=lambda x:x[1]['count'], reverse=True)
            # # bot.send_message(subscriber[1],'Recurring Tickers For ' + results['date'].max() + '\n\n' + tabulate(sortedcount,headers=['Ticker','Count','Marker']),parse_mode='HTML') #,tablefmt="grid"))
            #
            # results.sort_values(by=['marks'],ascending=False,inplace=True)
            # tosend = results[['ticker','marks','price']].set_index('ticker')
            # # bot.send_message(subscriber[1],'Marks\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
            #
            # results.sort_values(by=['late_marks'],ascending=False,inplace=True)
            # tosend = results[['ticker','late_marks','price']].set_index('ticker')
            # # bot.send_message(subscriber[1],'Late Marks\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))
            #
            # beware = 'Beware of these props:\n'
            # beware += 'Yesterday Loss: ' + str(results['Perc Yesterday Loss'].max()) + '\n'
            # beware += 'Sluggish Ticker: ' + str(results['Perc Sluggish Ticker'].max()) + '\n'
            # beware += 'Lower High: ' + str(results['Perc Lower High'].max()) + '\n'
            # # bot.send_message(subscriber[1],beware,parse_mode='HTML') #,tablefmt="grid"))
            #
            # perc_prop = []
            # for col in results.columns:
            #     if col[0:5] == 'Perc ':
            #         perc_prop.append(col)
            # max_prop = []
            # for col in perc_prop:
            #     cperf = {'Prop':col,'Perc':results[col].max()}
            #     max_prop.append(cperf)
            # max_prop.sort(key=lambda x: x['Perc'], reverse=True)
            # bot.send_message(subscriber[1],'Top Props:\n\n' + tabulate(max_prop[:20],headers='keys'),parse_mode='HTML')

            # results.sort_values(by=['first_range'],ascending=False,inplace=True)
            # tosend = results[['ticker','first_range','marks']].set_index('ticker')
            # bot.send_message(subscriber[1],'First Range\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            # results.sort_values(by=['first_body'],ascending=False,inplace=True)
            # tosend = results[['ticker','first_body','marks']].set_index('ticker')
            # bot.send_message(subscriber[1],'First Body\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            results.sort_values(by=['diff_level'],ascending=False,inplace=True)
            tosend = results[['ticker','diff_level']].set_index('ticker')
            bot.send_message(subscriber[1],'Diff Level\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            winlimit = 5
            curcount = {}
            results.sort_values(by=['first_body'],ascending=False,inplace=True)
            for ct in results.iloc[:winlimit].values:
                cticker = ct[0]
                if cticker in curcount:
                    curcount[cticker]['count'] += 1
                    curcount[cticker]['marker'] += 'b'
                else:
                    curcount[cticker] = {}
                    curcount[cticker]['count'] = 1
                    curcount[cticker]['marker'] = 'b'
                if len(results.loc[results['ticker']==cticker]):
                    curcount[cticker]['body'] = results.loc[results['ticker']==cticker]['first_body'].values[0]
                    curcount[cticker]['range'] = results.loc[results['ticker']==cticker]['first_range'].values[0]
                    curcount[cticker]['gap'] = results.loc[results['ticker']==cticker]['gap'].values[0]
                    curcount[cticker]['first_green'] = results.loc[results['ticker']==cticker]['First Green'].values[0]
            results.sort_values(by=['first_range'],ascending=False,inplace=True)
            for ct in results.iloc[:winlimit].values:
                cticker = ct[0]
                if cticker in curcount:
                    curcount[cticker]['count'] += 1
                    curcount[cticker]['marker'] += 'r'
                else:
                    curcount[cticker] = {}
                    curcount[cticker]['count'] = 1
                    curcount[cticker]['marker'] = 'r'
                if len(results.loc[results['ticker']==cticker]):
                    curcount[cticker]['body'] = results.loc[results['ticker']==cticker]['first_body'].values[0]
                    curcount[cticker]['range'] = results.loc[results['ticker']==cticker]['first_range'].values[0]
                    curcount[cticker]['gap'] = results.loc[results['ticker']==cticker]['gap'].values[0]
                    curcount[cticker]['first_green'] = results.loc[results['ticker']==cticker]['First Green'].values[0]
            results.sort_values(by=['gap'],ascending=False,inplace=True)
            for ct in results.iloc[:winlimit].values:
                cticker = ct[0]
                if cticker in curcount:
                    curcount[cticker]['count'] += 1
                    curcount[cticker]['marker'] += 'g'
                else:
                    curcount[cticker] = {}
                    curcount[cticker]['count'] = 1
                    curcount[cticker]['marker'] = 'g'
                if len(results.loc[results['ticker']==cticker]):
                    curcount[cticker]['body'] = results.loc[results['ticker']==cticker]['first_body'].values[0]
                    curcount[cticker]['range'] = results.loc[results['ticker']==cticker]['first_range'].values[0]
                    curcount[cticker]['gap'] = results.loc[results['ticker']==cticker]['gap'].values[0]
                    curcount[cticker]['first_green'] = results.loc[results['ticker']==cticker]['First Green'].values[0]

            sortedcount = sorted(curcount.items(), key=lambda x:x[1]['count'], reverse=True)
            print(tabulate(sortedcount,headers=['Ticker','Count','Marker','Body','Range','Gap']))
            bot.send_message(subscriber[1],'Recurring Range Tickers For ' + results['date'].max() + '\n\n' + tabulate(sortedcount,headers=['Ticker','Count','Marker','Body','Range','Gap']),parse_mode='HTML') #,tablefmt="grid"))

            yesterday = results.loc[results['Yesterday Status Barely']==1]
            yesterday = yesterday.loc[yesterday['2 Days Ago Status Barely']==1]
            yesterday.sort_values(by=['price'],inplace=True)
            tosend = yesterday[['ticker','price']]
            bot.send_message(subscriber[1],'2 Days Barely\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            yesterday = results.loc[results['Yesterday Status Barely']==1]
            yesterday = yesterday.loc[yesterday['2 Days Ago Status Barely']==0]
            yesterday.sort_values(by=['price'],inplace=True)
            tosend = yesterday[['ticker','price']]
            bot.send_message(subscriber[1],'Only Yesterday Barely\n\n' + tabulate(tosend.iloc[:10],headers="keys"),parse_mode='HTML') #,tablefmt="grid"))

            curcount = {}
            for day in range(6):
                results.sort_values(by=['Daily Green After ' + str(day+1) + ' Days Of Red'],ascending=False,inplace=True)
                fordays = results.loc[results['Daily Green After ' + str(day+1) + ' Days Of Red']==1]
                for ct in fordays.iloc[:winlimit].values:
                    cticker = ct[0]
                    curcount[cticker] = {}
                    curcount[cticker]['count'] = day + 1
            sortedcount = sorted(curcount.items(), key=lambda x:x[1]['count'], reverse=True)
            bot.send_message(subscriber[1],'Green After Red Days ' + results['date'].max() + '\n\n' + tabulate(sortedcount,headers=['Ticker','Count']),parse_mode='HTML') #,tablefmt="grid"))
