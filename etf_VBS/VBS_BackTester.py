
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from pykrx import stock


# 한 종목에 대한 BackTesting Module
class myBackTester():
    def __init__(self):
        self.df = ''

        self.code = ''
        self.unit_bid = ''

        self.fromDate = ''
        self.toDate = ''

        self.buy_report = ''
        self.sell_report = ''

        self.stay_profit = ''
        self.strat_profit_with_fee = ''

    def set_params(self, code, fromDate, toDate):
        self.code = code
        self.unit_bid = self.get_unit_bid_price(code)
        self.fromDate = fromDate
        self.toDate = toDate

        self.get_df()

    def get_unit_bid_price(self, code):
        opt = webdriver.ChromeOptions()
        opt.add_argument('headless')
        drv = webdriver.Chrome('./chromedriver.exe', options=opt)
        drv.implicitly_wait(3)
        base_url = 'https://finance.naver.com/item/sise.nhn?code='
        code = str(code)
        drv.get(base_url + code)
        bs = BeautifulSoup(drv.page_source, 'lxml')
        drv.quit()
        temp = bs.find_all('table', class_='type2')[1]
        sub_temp = temp.find_all('span', class_='tah p11 nv01')
        return int(sub_temp[7].get_text().strip().replace(',', '')) - int(
            sub_temp[9].get_text().strip().replace(',', ''))

    def get_df(self):
        self.df = stock.get_etf_ohlcv_by_date(self.fromDate, self.toDate, self.code)
        # 해당 종목의 Data 수가 부족한 경우:
        if len(self.df) < 50:
            return

    def set_strat(self, buy_strat='변동성 돌파', sell_strat='익일 시가'):
        # 해당 종목의 Data 수가 부족한 경우:
        if len(self.df) < 50:
            self.stay_sum = 'NA'
            self.strat_sum = 'NA'
            return

        # 매수 가격 기록
        buy_report = []
        # 매도 가격 기록
        sell_report = []

        # 매수 전략
        if buy_strat == '변동성 돌파':
            K = 0.5
            for i in range(1, len(self.df) - 1):
                yesterday_high = self.df.iloc[i - 1]['고가']
                yesterday_low = self.df.iloc[i - 1]['저가']
                yesterday_sweep = yesterday_high - yesterday_low
                target_price = self.df.iloc[i]['시가'] + yesterday_sweep * K
                # 매수 가격이 발생하였는지 확인
                if self.df.iloc[i]['저가'] < target_price < self.df.iloc[i]['고가']:
                    if target_price % self.unit_bid == 0:
                        buy_price = target_price
                    else:
                        buy_price = (target_price + self.unit_bid) // self.unit_bid * self.unit_bid
                    buy_report.append((i, buy_price))

        # 매도 전략
        # 익일 시가 매도
        if sell_strat == '익일 시가':
            for pnt in buy_report:
                sell_report.append((pnt[0] + 1, self.df.iloc[pnt[0] + 1]['시가']))

            # 수익률 계산
            stay_profit = (self.df.iloc[-1]['종가'] - self.df.iloc[0]['시가']) / self.df.iloc[0]['시가'] + 1
            strat_profit_with_fee = 1
            for i in range(len(buy_report)):
                delta = (0.99985 * sell_report[i][1] - 1.00015 * buy_report[i][1]) / buy_report[i][1]
                strat_profit_with_fee = strat_profit_with_fee * (1 + delta)

         # 당일 종가 매도
        if sell_strat == '당일 종가':
            for pnt in buy_report:
                sell_report.append((pnt[0], self.df.iloc[pnt[0]]['종가']))

            # 수익률 계산
            stay_profit = (self.df.iloc[-1]['종가'] - self.df.iloc[0]['시가']) / self.df.iloc[0]['시가'] + 1
            strat_profit_with_fee = 1
            for i in range(len(buy_report)):
                delta = (0.99985 * sell_report[i][1] - 1.00015 * buy_report[i][1]) / buy_report[i][1]
                strat_profit_with_fee = strat_profit_with_fee * (1 + delta)

        self.buy_report = buy_report
        self.sell_report = sell_report
        self.stay_profit = round(stay_profit, 4)
        self.strat_profit_with_fee = round(strat_profit_with_fee, 4)


# 종목 List에 대한 back_testing module
class AutoBackTester():
    def __init__(self):
        self.mBT = myBackTester()
        self.code_list = []
        self.company_list = []
        self.fromDate = ''
        self.toDate = ''
        self.stay_profit = []
        self.strat_profit_with_fee = []

    def set_params(self, code_list, company_list, fromDate, toDate):
        self.code_list = code_list
        self.company_list = company_list
        self.fromDate = fromDate
        self.toDate = toDate

    def start_backTesting(self):
        for i in range(len(self.code_list)):
            self.mBT.set_params(self.code_list[i], self.fromDate, self.toDate)
            self.mBT.set_strat(buy_strat='변동성 돌파', sell_strat='당일 종가')
            self.stay_profit.append(self.mBT.stay_profit)
            self.strat_profit_with_fee.append(self.mBT.strat_profit_with_fee)

    def save_data(self):
        # 총 거래일이 60인 미만의 주식 제거
        code_list = self.code_list
        company_list = self.company_list
        stay_profit = self.stay_profit
        strat_profit_with_fee = self.strat_profit_with_fee
        for idx, value in enumerate(stay_profit):
            if value == 'NA':
                del code_list[idx]
                del company_list[idx]
                del stay_profit[idx]
                del strat_profit_with_fee[idx]

        # Make Dir
        base_dir = './VBS_backTesting/'
        if not os.path.isdir(base_dir):
            os.mkdir(base_dir)

        data = {'code': code_list, 'company': company_list, '기간 수익': stay_profit,
                '전략 수익': strat_profit_with_fee}
        df = pd.DataFrame(data=data)
        writer = pd.ExcelWriter('./VBS_backTesting/profits.xlsx', engine='xlsxwriter')
        df.to_excel(writer)
        writer.close()




fromDate = '20190101'
toDate = '20210331'


df = pd.read_csv('ETFs.txt')
code_list = list(df['codes'])
for i in range(len(code_list)):
    code_list[i] = code_list[i][1:]
company_list = list(df['company'])
ABT = AutoBackTester()
ABT.set_params(code_list, company_list, fromDate, toDate)
ABT.start_backTesting()
ABT.save_data()

