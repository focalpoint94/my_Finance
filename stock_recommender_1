# stock_recommender.py

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
from Investar import Analyzer
import os
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
import matplotlib.font_manager as plt_fm
import boto3
import json

# Fonts for matplotlib
font_path = "C:/myPackage/font/godoFont_all/godoMaum.ttf"
font_prop = plt_fm.FontProperties(fname=font_path, size=18)

def post_message(slack_data):
    webhook_url = '*************************************************'
    response = requests.post(webhook_url, data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text))

def get_url_of_image(image):
    bucket_name = "mystock"
    region = "us-east-2"
    df = pd.read_csv('amazon_s3.csv')
    aws_access_key_id = df.at[0, 'Access key ID']
    aws_secret_access_key = df.at[0, 'Secret access key']
    client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    data = open(image, 'rb')
    client.put_object(Body=data, Bucket=bucket_name, Key=image, ACL='public-read',
                  ContentType='image/png', ContentDisposition='inline')

    url = "https://mystock.s3.us-east-2.amazonaws.com/C%3A/" + image[3:]
    return url

def search_stocks():
    code_list = []
    company_list = []
    url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok="
    with urlopen(url) as doc:
        html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
        pgrr = html.find('td', class_='pgRR')
        s = str(pgrr.a['href']).split('=')
        last_page = s[-1]
    for sosok in range(2):
        for page in range(1, 3):
            page_url = '{}{}&page={}'.format(url, sosok, page)
            with urlopen(page_url) as doc:
                html = BeautifulSoup(requests.get(page_url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
                html_partial = html.find_all('td', class_='no')
                for i in range(len(html_partial)):
                    temp = html_partial[i].parent
                    x = str(temp.a['href']).split('=')[-1]
                    if not x.isdigit():
                        continue
                    code_list.append(int(x))
                    company_list.append(temp.a.get_text())
    code_list = list(map('{:06d}'.format, code_list))

    # Make Dir
    base_dir = 'C:/myResult/'
    tdate = datetime.now().strftime('%Y%m%d')
    date_dir = base_dir + tdate
    if not os.path.isdir(date_dir):
        os.mkdir(date_dir)

    for idx, company in enumerate(company_list):
        mk = Analyzer.MarketDB()
        company_name = company
        df = pd.DataFrame()
        tmnow = datetime.now()
        tmpast = (tmnow - timedelta(days=500)).strftime('%Y-%m-%d')
        df = mk.get_daily_price(company_name, tmpast)

        # MACD Histogram
        ema60 = df.close.ewm(span=60).mean()
        ema130 = df.close.ewm(span=130).mean()
        macd = ema60 - ema130
        signal = macd.ewm(span=45).mean()
        macdhist = macd - signal
        df = df.assign(ema130=ema130, ema60=ema60, macd=macd, signal=signal, macdhist=macdhist).dropna()
        df['number'] = df.index.map(mdates.date2num)
        ohlc = df[['number', 'open', 'high', 'low', 'close']]

        # Bollinger Band
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        df['stddev'] = df['close'].rolling(window=20).std()
        df['upper'] = df['MA20'] + (df['stddev'] * 2)
        df['lower'] = df['MA20'] - (df['stddev'] * 2)
        df['PB'] = (df['close'] - df['lower']) / (df['upper'] - df['lower'])

        # Defined Golden Cross
        dates = ''
        pbs = ''
        if len(df.close) < 7:
            continue
        for i in range(len(df.close)-7, len(df.close)):
            if macdhist[i] - macdhist[i-1] > 80 and df.MA20[i] > df.MA20[i-20] and df.MA60[i] > df.MA60[i-60]:
                dates = dates + (df.date[i].strftime("%Y-%m-%d") + ', ')
                pbs = pbs + (str(df.PB[i]) + ', ')

        # If no defined Golden Cross:
        if not dates:
            continue

        dates = dates[:-2]
        pbs = pbs[:-2]

        # Make Dir
        company_dir = date_dir + '/' + code_list[idx]
        if not os.path.isdir(company_dir):
            os.mkdir(company_dir)

        # Figure1
        figure1 = plt.figure(1, figsize=(9, 9))
        p1 = plt.subplot(2, 1, 1)
        plt.title(company_name, fontproperties=font_prop)
        plt.grid(True)
        candlestick_ohlc(p1, ohlc.values, width=.6, colorup='red', colordown='blue')
        p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.plot(df.number, df['MA20'], 'k--', label='Moving Avg 20')
        plt.plot(df.number, df['MA60'], 'g--', label='Moving Avg 60')
        plt.plot(df.number, df['ema130'], color='c', label='EMA130')
        for i in range(1, len(df.close)):
            if macdhist[i] - macdhist[i-1] > 80 and df.MA20[i] > df.MA20[i-20] and df.MA60[i] > df.MA60[i-60]:
                plt.plot(df.number.values[i], df.close.min(), 'r^')
        plt.legend(loc='best')
        p2 = plt.subplot(2, 1, 2)
        plt.grid(True)
        p2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.bar(df.number, df['macdhist'], color='m', label='MACD-Hist')
        plt.plot(df.number, df['macd'], color='b', label='MACD')
        plt.plot(df.number, df['signal'], 'g--', label='MACD-Signal')
        for i in range(1, len(df.close)):
            if macdhist[i] - macdhist[i-1] > 80 and df.MA20[i] > df.MA20[i-20] and df.MA60[i] > df.MA60[i-60]:
                plt.plot(df.number.values[i], df.macd.min(), 'r^')
        plt.legend(loc='best')
        figure1.savefig(fname=company_dir+'/fig1', dpi=300)
        plt.close()

        # Figure2
        figure2 = plt.figure(2, figsize=(9,8))
        plt.subplot(2, 1, 1)
        plt.plot(df.index, df['close'], color='#0000ff', label='Close')
        plt.plot(df.index, df['upper'], 'r--', label='Upper Band')
        plt.plot(df.index, df['MA20'], 'k--', label='Moving Avg 20')
        plt.plot(df.index, df['MA60'], 'g--', label='Moving AVG 60')
        plt.plot(df.index, df['lower'], 'c--', label='Lower Band')
        plt.fill_between(df.index, df['upper'], df['lower'], color='0.9')
        for i in range(1, len(df.close)):
            if macdhist[i] - macdhist[i-1] > 80 and df.MA20[i] > df.MA20[i-20] and df.MA60[i] > df.MA60[i-60]:
                plt.plot(df.number.values[i], df.close.min(), 'r^')
        plt.legend(loc='best')
        plt.title(company_name + '\'s ' + 'Bollinger Band (20-day, 2-std)', fontproperties=font_prop)
        plt.subplot(2, 1, 2)
        plt.plot(df.index, df['PB'], color='b', label='%B')
        for i in range(1, len(df.close)):
            if macdhist[i] - macdhist[i-1] > 80 and df.MA20[i] > df.MA20[i-20] and df.MA60[i] > df.MA60[i-60]:
                plt.plot(df.number.values[i], df.PB.min(), 'r^')
        plt.grid(True)
        plt.legend(loc='best')
        figure2.savefig(fname=company_dir+'/fig2', dpi=300)
        plt.close()

        # URLs of two figures
        fig1_path = company_dir + '/fig1.png'
        fig2_path = company_dir + '/fig2.png'
        fig1_url = get_url_of_image(fig1_path)
        fig2_url = get_url_of_image(fig2_path)

        # Slack Msg Formatting
        slack_data = dict()
        blocks = []
        blocks.append({
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": '종목: ' + company_name + ' ' + '(코드: ' + code_list[idx] + ')',
				"emoji": True
			}
		})
        blocks.append({
			"type": "section",
			"fields": [
				{
					"type": "mrkdwn",
					"text": "*최근 7 개장일 중 Golden Cross 날짜*\n" + dates
				},
				{
					"type": "mrkdwn",
					"text": "*각 날짜의 PB Value*\n" +pbs
				}
			]
		})
        blocks.append(
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "MACD Histogram",
                    "emoji": True
                },
                "image_url": fig1_url,
			    "alt_text": "MACD Histogram"
            }
        )
        blocks.append(
            {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Bollinger Band",
                    "emoji": True
                },
                "image_url": fig2_url,
			    "alt_text": "Bollinger Band"
            }
        )
        slack_data['blocks'] = blocks
        post_message(slack_data)

def date_report():
    starter_data = dict()
    blocks = []
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "{} Recommendations".format(datetime.now().strftime('%Y-%m-%d')),
            "emoji": True
        }
    })
    starter_data['blocks'] = blocks
    post_message(starter_data)

if __name__ == '__main__':
    date_report()
    search_stocks()
