
from Investar import Analyzer

import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.font_manager as plt_fm
import matplotlib.dates as mdates

from mpl_finance import candlestick_ohlc

import os

from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

from selenium import webdriver

font_path = "./font/godoFont_all/godoMaum.ttf"
font_prop = plt_fm.FontProperties(fname=font_path, size=18)


# 한 종목에 대한 back-testing module
#
class myBackTester():
    def __init__(self):
        self.mk = Analyzer.MarketDB()
        self.df = ''
        self.ohlc = ''

        self.isStock = ''
        self.code = ''
        self.company = ''
        self.fromDate = ''
        self.recallDate = ''
        self.toDate = ''

        self.buy_report = ''
        self.sell_report = ''
        self.stay_sum = ''
        self.strat_sum = ''
        self.strat_sum_with_fee = ''

    def set_params(self, isStock, code, company, fromDate, toDate):
        self.isStock = isStock
        self.code = code
        self.company = company
        self.fromDate = fromDate
        recallDate = datetime.strptime(fromDate, "%Y-%m-%d").date()
        self.recallDate = str(recallDate - timedelta(days=100))
        self.toDate = toDate

        self.get_df()


    def get_df(self):
        self.df = self.mk.get_daily_price(self.code, self.recallDate, self.toDate)
        # 해당 종목의 Data 수가 부족한 경우:
        if len(self.df) < 60:
            return

        for i in range(len(self.df)):
            if self.df.index[i] > datetime.strptime(self.fromDate, "%Y-%m-%d").date():
                break

        self.df['number'] = self.df.index.map(mdates.date2num)

        # Bollinger Band
        self.df['MA3'] = self.df['close'].rolling(window=3).mean()
        self.df['MA5'] = self.df['close'].rolling(window=5).mean()
        self.df['MA10'] = self.df['close'].rolling(window=10).mean()
        self.df['MA20'] = self.df['close'].rolling(window=20).mean()
        self.df['MA60'] = self.df['close'].rolling(window=60).mean()
        #self.df['MA120'] = self.df['close'].rolling(window=120).mean()
        self.df['stddev'] = self.df['close'].rolling(window=20).std()
        self.df['upper'] = self.df['MA20'] + (self.df['stddev'] * 2)
        self.df['lower'] = self.df['MA20'] - (self.df['stddev'] * 2)
        self.df['PB'] = (self.df['close'] - self.df['lower']) / (self.df['upper'] - self.df['lower'])

        # MACD Histogram
        ema60 = self.df.close.ewm(span=60).mean()
        ema130 = self.df.close.ewm(span=130).mean()
        macd = ema60 - ema130
        signal = macd.ewm(span=45).mean()
        macdhist = macd - signal
        self.df = self.df.assign(ema130=ema130, ema60=ema60, macd=macd, signal=signal, macdhist=macdhist)

        self.df = self.df[i:]

        # OHLC
        self.ohlc = self.df[['number', 'open', 'high', 'low', 'close']]


    def set_strat(self, buy_strat=0, sell_strat=0):
        # 해당 종목의 Data 수가 부족한 경우:
        if len(self.df) < 60:
            self.stay_sum = 'NA'
            self.strat_sum = 'NA'
            return

        # 매수 시점 기록 (날짜 idx, 가격)
        buy_report = []
        # 매도 시점 기록 (날짜 idx, 가격)
        sell_report = []

        # 매수 전략
        # 0. 변동성 돌파 전략
        if buy_strat == 0:
            K = 0.295
            for i in range(1, len(self.df) - 1):
                yesterday_high = self.df.iloc[i - 1]['high']
                yesterday_low = self.df.iloc[i - 1]['low']
                yesterday_sweep = yesterday_high - yesterday_low
                target_price = self.df.iloc[i]['open'] + yesterday_sweep * K
                # 매수 가격이 발생하였는지 확인
                if self.df.iloc[i]['low'] < target_price < self.df.iloc[i]['high']:
                    buy_report.append((i, target_price))

        # 1. 변동성 돌파 전략 (with moving average condition)
        # 5일 및 20일 이격도 조건 추가
        if buy_strat == 1:
            K = 0.295
            for i in range(1, len(self.df) - 1):
                yesterday_high = self.df.iloc[i - 1]['high']
                yesterday_low = self.df.iloc[i - 1]['low']
                yesterday_sweep = yesterday_high - yesterday_low
                target_price = self.df.iloc[i]['open'] + yesterday_sweep * K
                # 매수 가격이 발생하였는지 확인
                if self.df.iloc[i]['low'] < target_price < self.df.iloc[i]['high'] and \
                        self.df.iloc[i - 1]['close'] / self.df.iloc[i - 1]['MA20'] > 1.05 and \
                        self.df.iloc[i - 1]['close'] / self.df.iloc[i - 1]['MA5'] > 1.05:
                    buy_report.append((i, target_price))

        # 매도 전략
        # 0. 익일 시가 매도
        if sell_strat == 0:
            for pnt in buy_report:
                sell_report.append((pnt[0] + 1, self.df.iloc[pnt[0] + 1]['open']))

            # 수익률 계산
            stay_sum = (self.df.iloc[-1]['close'] - self.df.iloc[0]['open']) / self.df.iloc[0]['open'] + 1
            strat_sum = 1
            for i in range(len(buy_report)):
                delta = (sell_report[i][1] - buy_report[i][1]) / buy_report[i][1]
                strat_sum = strat_sum * (1 + delta)
            if self.isStock:
                strat_sum_with_fee = 1
                for i in range(len(buy_report)):
                    delta = (0.99685*sell_report[i][1] - 1.00015*buy_report[i][1]) / buy_report[i][1]
                    strat_sum_with_fee = strat_sum_with_fee * (1 + delta)
            else:
                strat_sum_with_fee = 1
                for i in range(len(buy_report)):
                    delta = (0.99985 * sell_report[i][1] - 1.00015 * buy_report[i][1]) / buy_report[i][1]
                    strat_sum_with_fee = strat_sum_with_fee * (1 + delta)

        # 2. 익일 시가 매도
        # 매도 가격이 매수 가격보다 낮은 경우 -> 존버
        # 매수 가격보다 5% 이상 하락시 -> 손절매
        # 잔량 -> 지정 기간의 마지막날 모두 매도
        if sell_strat == 1:
            for pnt in buy_report:
                stoploss_price = pnt[1] * 0.95
                # 매수 시점 다음날부터
                # 시가 > 매수가이면, 매도
                # 시가 < stoploss_price이면, 매도
                sell_flag = False
                for d in range(pnt[0] + 1, len(self.df)):
                    if self.df.iloc[d]['open'] > pnt[1]:
                        sell_report.append((d, self.df.iloc[d]['open']))
                        sell_flag = True
                        break
                    elif self.df.iloc[d]['open'] < stoploss_price:
                        sell_report.append((d, stoploss_price))
                        sell_flag = True
                        break
                if not sell_flag:
                    sell_report.append((len(self.df)-1, self.df.iloc[-1]['open']))

            # 수익률 계산
            stay_sum = (self.df.iloc[-1]['close'] - self.df.iloc[0]['open']) / self.df.iloc[0]['open'] + 1
            strat_sum = 1
            for i in range(len(buy_report)):
                delta = (sell_report[i][1] - buy_report[i][1]) / buy_report[i][1]
                strat_sum = strat_sum * (1 + delta)
            if self.isStock:
                strat_sum_with_fee = 1
                for i in range(len(buy_report)):
                    delta = (0.99685 * sell_report[i][1] - 1.00015 * buy_report[i][1]) / buy_report[i][1]
                    strat_sum_with_fee = strat_sum_with_fee * (1 + delta)
            else:
                strat_sum_with_fee = 1
                for i in range(len(buy_report)):
                    delta = (0.99985 * sell_report[i][1] - 1.00015 * buy_report[i][1]) / buy_report[i][1]
                    strat_sum_with_fee = strat_sum_with_fee * (1 + delta)


        self.buy_report = buy_report
        self.sell_report = sell_report
        self.stay_sum = round(stay_sum, 4)
        self.strat_sum = round(strat_sum, 4)
        self.strat_sum_with_fee = round(strat_sum_with_fee, 4)



    def plot_graph(self):
        # 해당 종목의 Data 수가 부족한 경우:
        if len(self.df) < 60:
            return

        figure1 = plt.figure(1, figsize=(9, 9))
        p1 = plt.subplot(1, 1, 1)
        plt.title(self.code + ' ' + self.company, fontproperties=font_prop)
        plt.grid(True)
        candlestick_ohlc(p1, self.ohlc.values, width=.6, colorup='red', colordown='blue')
        p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.plot(self.df.number, self.df['MA5'], 'b--', label='Moving Avg 5')
        plt.plot(self.df.number, self.df['MA20'], 'k--', label='Moving Avg 20')
        plt.plot(self.df.number, self.df['MA60'], 'g--', label='Moving Avg 60')
        #plt.plot(self.df.number, self.df['MA120'], 'c--', label='Moving AVG 120')
        for pnt in self.buy_report:
            # plt.plot(self.df.number.values[pnt[0]],
            #          min(self.df.close.min(), self.df['MA20'].min(), self.df['MA60'].min()), 'r^')
            plt.plot(self.df.number.values[pnt[0]],
                      0.95*self.df.close.min(), 'r^')
        for pnt in self.sell_report:
        #     # plt.plot(self.df.number.values[pnt[0]],
        #     #          min(self.df.close.min(), self.df['MA20'].min(), self.df['MA60'].min()), 'b^')
            plt.plot(self.df.number.values[pnt[0]],
                     0.90 * self.df.close.min(), 'b^')
        plt.text(self.df['number'][-15], min(self.df.close.min(), self.df['MA20'].min()),
                 "기간 수익: {}\n전략 수익: {}\n전략 수익(수수료 O): {}".format(self.stay_sum, self.strat_sum, self.strat_sum_with_fee),
                 fontsize=10, fontproperties=font_prop)
        plt.legend(loc='best')
        if not os.path.isdir('./backTester'):
            os.mkdir('./backTester')
        figure1.savefig(fname='./backTester/' + self.code, dpi=300)
        plt.close()


# 종목 List에 대한 back_testing module
class AutoBackTester():
    def __init__(self):
        self.mBT = myBackTester()
        self.isStock = ''
        self.code_list = []
        self.company_list = []
        self.fromDate = ''
        self.toDate = ''
        self.stay_sum = []
        self.strat_sum = []
        self.strat_sum_with_fee = []


    def set_params(self, isStock, code_list, company_list, fromDate, toDate):
        self.isStock = isStock
        self.code_list = code_list
        self.company_list = company_list
        self.fromDate = fromDate
        self.toDate = toDate


    def start_backTesting(self):
        for i in range(len(self.code_list)):
            self.mBT.set_params(self.isStock, self.code_list[i], self.company_list[i], self.fromDate, self.toDate)
            self.mBT.set_strat()
            self.mBT.plot_graph()
            self.stay_sum.append(self.mBT.stay_sum)
            self.strat_sum.append(self.mBT.strat_sum)
            self.strat_sum_with_fee.append(self.mBT.strat_sum_with_fee)


    def save_yields(self):
        # 총 거래일이 60인 미만의 주식 제거
        code_list = self.code_list
        company_list = self.company_list
        stay_sum = self.stay_sum
        strat_sum = self.strat_sum
        strat_sum_with_fee = self.strat_sum_with_fee
        for idx, value in enumerate(stay_sum):
            if value == 'NA':
                del code_list[idx]
                del company_list[idx]
                del stay_sum[idx]
                del strat_sum[idx]
                del strat_sum_with_fee[idx]
        
        data = {'code': code_list, 'company': company_list, '기간 수익': stay_sum,
                '전략 수익': strat_sum, '전략 수익(수수료 고려)': strat_sum_with_fee}
        df = pd.DataFrame(data=data)
        writer = pd.ExcelWriter('./backTester/yields.xlsx', engine='xlsxwriter')
        df.to_excel(writer)
        writer.close()


# 종목 List를 선정하는 class
class SetStockLists():
    def __init__(self, type='주식시가총액'):
        self.code_list = []
        self.company_list = []

        """
        type0: 시가 총액 기준
        
        """
        if type == '주식시가총액':
            self.code_list, self.company_list = self.by_market_capitalization()

        elif type == 'ETF거래량':
            self.code_list, self.company_list = self.by_ETF_Volume()


    def by_market_capitalization(self, use_Kosdaq=False, num_company=50):
        code_list = []
        company_list = []
        url = "https://finance.naver.com/sise/sise_market_sum.nhn?sosok="
        with urlopen(url) as doc:
            html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
            pgrr = html.find('td', class_='pgRR')
            s = str(pgrr.a['href']).split('=')
            last_page = s[-1]
        if use_Kosdaq:
            sosok_limit = 2
        else:
            sosok_limit = 1
        page_limit = num_company // 50 + 2
        for sosok in range(sosok_limit):
            for page in range(1, page_limit):
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

        code_list = code_list[:num_company]
        company_list = company_list[:num_company]
        return code_list, company_list


    def by_ETF_Volume(self, num_company=100):
        opt = webdriver.ChromeOptions()
        opt.add_argument('headless')
        drv = webdriver.Chrome('./chromedriver.exe', options=opt)
        drv.implicitly_wait(3)
        drv.get('https://finance.naver.com/sise/etf.nhn')

        bs = BeautifulSoup(drv.page_source, 'lxml')
        drv.quit()

        # df: 거래량 기준 모든 ETF
        table = bs.find_all('table', class_='type_1 type_etf')
        df = pd.read_html(str(table), header=0)[0]
        df = df.drop(columns=['Unnamed: 9'])
        df = df.dropna()
        df = df.sort_values(by='거래량', ascending=False)
        etf_td = bs.find_all('td', class_='ctg')
        etfs = {}
        for td in etf_td:
            s = str(td.a['href']).split('=')
            code = s[-1]
            etfs[td.a.text] = code
        company_names = []
        codes = []
        for i in range(len(df)):
            name = df.iloc[i]['종목명']
            company_names.append(name)
            codes.append(etfs[name])
        df.insert(1, 'code', codes)

        return list(df['code'][:num_company]), list(df['종목명'][:num_company])




SSL = SetStockLists(type='ETF거래량')
code_list = SSL.code_list
company_list = SSL.company_list

ABT = AutoBackTester()
fromDate = '2021-01-01'
toDate = '2021-03-31'

"""
isStock: 주식(True), ETF(False) -> 수수료 적용

"""
ABT.set_params(isStock=False, code_list=code_list, company_list=company_list,
               fromDate=fromDate, toDate=toDate)
ABT.start_backTesting()
ABT.save_yields()




