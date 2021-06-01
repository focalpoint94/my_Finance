
from pykrx import stock
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from time import sleep
import numpy as np
import OpenDartReader
import math


"""
Functions
"""
def debt_ratio(code: str, year: str):
    """
    :param code: company code
    :param year: fiscal year
    :return: 자본, 부채, 부채 비율
    """
    api_key = '***************************************'
    dart = OpenDartReader(api_key)
    df = dart.finstate(code, year)
    if df is None or df.empty:
        return 9999
    fs_cfs = df[df['fs_div'].str.contains('CFS')]
    if fs_cfs.empty:
        return 9999
    fs_bs = fs_cfs[fs_cfs['sj_div'].str.contains('BS')]
    fs_equity = fs_bs[fs_bs['account_nm'].str.contains('자본총계')]
    fs_debt = fs_bs[fs_bs['account_nm'].str.contains('부채총계')]
    equity = fs_equity[['thstrm_amount']].iloc[0, 0].replace(',', '').strip()
    debt = fs_debt[['thstrm_amount']].iloc[0, 0].replace(',', '').strip()
    return int(debt) / int(equity)


def calc_yield(**args):
    """
    :param args: dictionary
    <keys>
    test_year = "2018"
    test_month = "11"
    PER_threshold = 5
    debt_ratio_threshold = 50
    num_stock_limit = 30
    upper_yield_limit = 50
    duration = 2 (year)

    :return: 평균 수익률, 동기간 코스피 수익률
    """
    test_year = args['test_year']
    test_month = args['test_month']
    PER_threshold = args['PER_threshold']
    debt_ratio_threshold = args['debt_ratio_threshold']
    num_stock_limit = args['num_stock_limit']
    upper_yield_limit = args['upper_yield_limit']
    duration = args['duration']  # duration unit: year

    tax_rate = 0.00315
    test_date = test_year + test_month + "01"
    test_end_date = min(str(int(test_year) + duration) + test_month + "01",
                        datetime.strftime(datetime.now().date(), "%Y%m%d"))
    test_date = stock.get_nearest_business_day_in_a_week(date=test_date, prev=False)
    test_end_date = stock.get_nearest_business_day_in_a_week(date=test_end_date, prev=True)

    """
    Loading Data
    """
    df1 = stock.get_market_fundamental_by_ticker(test_date, market="KOSPI")
    df2 = stock.get_market_fundamental_by_ticker(test_date, market="KOSDAQ")
    df = pd.concat([df1, df2])
    df = df[(df['PER'] < PER_threshold) & (df['PER'] > 0)]
    df = df.sort_values(by='PER', ascending=True)
    df = df[['PER']]
    code_list = df.index.to_list()
    lowPBR_with_lowDebt_list = []
    PER_list = []
    debt_list = []
    for code in code_list:
        _debt_ratio = debt_ratio(code, test_year)
        if 0 < _debt_ratio < debt_ratio_threshold / 100:
            lowPBR_with_lowDebt_list.append(code)
            PER_list.append(df.loc[code]['PER'])
            debt_list.append(_debt_ratio)
        sleep(1)

    """
    lowPBR_with_lowDebt_list: The Basket (Low PER with Low Debt List)
    PER_list: PER 값
    debt_list: debt 값
    name_list: 종목명
    buy_price: 매수 가격
    sell_price: 매도 가격
    
    매수: Test Date 시가 매수
    익절 조건: 상한 수익률 돌파 시
    손절 조건: duration 기간 말
    """
    lowPBR_with_lowDebt_list = lowPBR_with_lowDebt_list[:num_stock_limit]
    PER_list = PER_list[:num_stock_limit]
    debt_list = debt_list[:num_stock_limit]
    name_list = []
    buy_price = []
    sell_price = []
    yield_list = []

    for code in lowPBR_with_lowDebt_list:
        name = stock.get_market_ticker_name(code)
        name_list.append(name)
        temp = stock.get_market_ohlcv_by_date(test_date, test_date, code)
        bought_price = temp.iloc[0]['시가']
        buy_price.append(bought_price)
        sleep(1)

    """
    수익률 계산
    """
    for i, code in enumerate(lowPBR_with_lowDebt_list):
        df = stock.get_market_ohlcv_by_date(test_date, test_end_date, code)
        target_price = buy_price[i] * (1 + upper_yield_limit / 100)
        sold = False
        for j in range(len(df)):
            if df.iloc[j]['저가'] <= target_price <= df.iloc[j]['고가']:
                sold_price = target_price
                sell_price.append(sold_price)
                sold = True
                break
        if not sold:
            sold_price = df.iloc[-1]['종가']
            sell_price.append(sold_price)
        sleep(1)

    for i in range(len(lowPBR_with_lowDebt_list)):
        yield_with_tax = ((1 - tax_rate) * sell_price[i] - (1 + tax_rate) * buy_price[i]) / buy_price[i] + 1
        yield_list.append(yield_with_tax)

    """
    NAN Check
    """
    _yield_list = [_yield for _yield in yield_list if not math.isnan(_yield)]

    kospi = stock.get_index_ohlcv_by_date(test_date, test_end_date, "1001")
    kospi_yield = (kospi.iloc[-1]['종가'] - kospi.iloc[0]['시가']) / kospi.iloc[0]['시가'] + 1

    print("* Low PBR with Low Debt 전략")
    print("* 기간: ", test_date + ' ~ ' + test_end_date)
    print("* 종목: ", lowPBR_with_lowDebt_list)
    print("* 종목명: ", name_list)
    print("* PER: ", PER_list)
    print("* Debt Ratio: ", debt_list)
    print("* 종목 수익률: ", yield_list)
    print("* 평균 수익률: ", round(np.mean(_yield_list), 4))
    print("* 동기간 코스피 수익률: ", round(kospi_yield, 4))

    return round(np.mean(_yield_list), 4), round(kospi_yield, 4)


"""
Hyper Params
"""
start_year = 2015
end_year = 2019

"""
Execution
"""
term_list = []
y1_list = []
y2_list = []
for year in range(start_year, end_year + 1):
    test_year = str(year)
    test_month = "01"
    PER_threshold = 5
    debt_ratio_threshold = 50
    num_stock_limit = 30
    upper_yield_limit = 50
    duration = 2 # duration unit: year
    params = dict()
    params['test_year'] = test_year
    params['test_month'] = test_month
    params['PER_threshold'] = PER_threshold
    params['debt_ratio_threshold'] = debt_ratio_threshold
    params['num_stock_limit'] = num_stock_limit
    params['upper_yield_limit'] = upper_yield_limit
    params['duration'] = duration
    term = test_year + '년' + test_month + '월' + ' (최대 보유 기간: ' + str(duration) + '년)'
    y1, y2 = calc_yield(**params)
    term_list.append(term)
    y1_list.append(y1)
    y2_list.append(y2)

data = {'Term': term_list, '전략 수익률': y1_list, '동기간 코스피 수익률': y2_list}
df = pd.DataFrame(data=data)
writer = pd.ExcelWriter('./results.xlsx', engine='xlsxwriter')
df.to_excel(writer)
writer.close()

