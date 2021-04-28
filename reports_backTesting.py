
import os

import pandas as pd

from pykrx import stock

from datetime import datetime

from mpl_finance import candlestick_ohlc

import matplotlib.pyplot as plt
import matplotlib.font_manager as plt_fm
import matplotlib.dates as mdates

from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests


font_path = "./font/godoFont_all/godoMaum.ttf"
font_prop = plt_fm.FontProperties(fname=font_path, size=18)


def get_reports():
    url = "https://finance.naver.com/research/company_list.nhn?&page="
    with urlopen(url) as doc:
        html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
        pgrr = html.find('td', class_='pgRR')
        s = str(pgrr.a['href']).split('=')
        last_page = s[-1]

        code_lists = []
        name_lists = []
        link_lists = []
        title_lists = []
        company_lists = []
        pdf_lists = []
        date_lists = []
        price_lists = []
        opi_lists = []

        page_limit = 1000
        for page in range(1, page_limit + 1):
            page_url = url + str(page)
            with urlopen(page_url) as doc:
                html = BeautifulSoup(requests.get(page_url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
                html = html.find('table', class_="type_1")
                lists = html.find_all('tr')
                lists = lists[2:]

                for i in range(len(lists)):
                    if lists[i].td.get_text() != '':
                        code = lists[i].a['href'].split('=')[-1]
                        name = lists[i].a['title']
                        link = "https://finance.naver.com/research/" + \
                               lists[i].find_all('td')[1].a['href']
                        title = lists[i].find_all('td')[1].a.get_text()
                        company = lists[i].find_all('td')[2].get_text()
                        if lists[i].find_all('td')[3].a:
                            pdf = lists[i].find_all('td')[3].a['href']
                        else:
                            pdf = "N/A"
                        date = lists[i].find_all('td')[4].get_text()
                        with urlopen(link) as doc:
                            html = BeautifulSoup(requests.get(link, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
                            html = html.find('div', class_='view_info')
                            price = html.em.get_text().replace(',', '')
                            opi = html.find('em', class_='coment').get_text()

                        """
                        포함 조건
                        - 유효한 증권 회사의 리포트
                        effective_companys = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권', '키움증권']
                        - 목표가 제시                    
                        """

                        effective_companys = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권', '키움증권' ]

                        if company not in effective_companys:
                            continue
                        if price == '없음':
                            continue

                        code_lists.append(code)
                        name_lists.append(name)
                        link_lists.append(link)
                        title_lists.append(title)
                        company_lists.append(company)
                        pdf_lists.append(pdf)
                        date_lists.append(date)
                        price_lists.append(price)
                        opi_lists.append(opi)

        data = {'code': code_lists, 'stock': name_lists, 'link': link_lists, 'title': title_lists,
                'company': company_lists, 'pdf': pdf_lists, 'date': date_lists, 'target price': price_lists,
                'opinion': opi_lists}
        df = pd.DataFrame(data=data)
        df = df.sort_values(by='code', ascending=True)
        writer = pd.ExcelWriter('./reports.xlsx', engine='xlsxwriter')
        df.to_excel(writer)
        writer.close()


def read_reports():
    df = pd.read_excel('reports.xlsx', engine='openpyxl', index_col=0)
    df = df.sort_values(by='date', ascending=True)
    df['code'] = df['code'].map('{:06d}'.format)

    stocks = dict()
    num_company = 5
    company_list = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권', '키움증권']

    for i in range(len(df)):
        data = df.iloc[i]
        code = data['code']
        date = data['date']
        tp = data['target price']
        opi = data['opinion']

        if not stocks.get(code):
            stocks[code] = [[] for _ in range(num_company)]

        for j in range(num_company):
            if company_list[j] == data['company']:
                break
        stocks[code][j].append((date, tp, opi))

    return stocks


def plot_graph():
    if not os.path.isdir('./graphs'):
        os.mkdir('./graphs')

    stocks = read_reports()
    for key, value in stocks.items():
        code = key
        """
        value[0]: 하나금융투자
        value[1]: 이베스트증권
        value[2]: IBK투자증권
        value[3]: 미래에셋증권
        value[4]: 키움증권
        """
        # 주가
        df = stock.get_market_ohlcv_by_date("20180101", "20210423", code)
        df['number'] = df.index.map(mdates.date2num)
        # 코스피
        kospi = stock.get_index_ohlcv_by_date("20180101", "20210423", "1001")
        kospi['number'] = kospi.index.map(mdates.date2num)
        # Empty df인 경우
        if df.empty:
            continue
        name = stock.get_market_ticker_name(code)
        # 거래 정지 기간 처리
        idx_list = df.index[df.시가 == 0]
        for idx in idx_list:
            close = df.loc[idx].종가
            df.at[idx, '시가'] = close
            df.at[idx, '고가'] = close
            df.at[idx, '저가'] = close
        ohlc = df[['number', '시가', '고가', '저가', '종가']]
        figure1 = plt.figure(1, figsize=(9, 9))
        p1 = plt.subplot(1, 1, 1)
        plt.title(code + ' ' + name)
        # plt.grid(True)
        candlestick_ohlc(p1, ohlc.values, width=.6, colorup='red', colordown='blue')
        p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        for i in range(1):
            for j in range(1, len(value[i])):
                val = value[i][j]
                day = val[0]
                tp = val[1]
                tp_past = value[i][j - 1][1]
                day = mdates.date2num(datetime.strptime(day, "%y.%m.%d").date())
                if tp > tp_past:
                    if i == 0:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='green', linewidth=1)
                    elif i == 1:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='pink', linewidth=1)
                    elif i == 2:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='purple', linewidth=1)
                    elif i == 3:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='grey', linewidth=1)
                    else:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='orange', linewidth=1)
                    # plt.plot(day, df.종가.min(), 'r^')
        p2 = p1.twinx()
        p2.plot(kospi['number'], kospi['종가'], linewidth=1, label='KOSPI')
        plt.legend(loc='best')
        figure1.savefig(fname='./graphs/' + code, dpi=300)
        plt.close()


#get_reports()
plot_graph()

