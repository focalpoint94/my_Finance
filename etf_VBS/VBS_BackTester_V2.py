
"""
VBS_BackTester_V2.py
Volatility Break-Through BackTest
<Functions>
1) 개별 종목의 yield 분포
2) 일평균 매수 종목 수 분포
3) 일 평균 전략 평균 수익률 분포
4) 누적 수익률
"""
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from pykrx import stock
import matplotlib.pyplot as plt

"""
Load code list from ETFs.txt
"""
df = pd.read_csv('ETFs.txt')
code_list = list(df['codes'])
for i in range(len(code_list)):
    code_list[i] = code_list[i][1:]

"""
Functions
"""
def get_unit_bid_price(code):
    """
    :param code: 종목 코드
    :return: 단위 호가
    """
    opt = webdriver.ChromeOptions()
    opt.add_argument('headless')
    opt.add_argument('--no-sandbox')
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

def calc_yield(**kwargs):
    """
    :param kwargs:
    code: 종목 코드
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    :return:
    매수 리스트 [(df index, 매수가격), ...]
    매도 리스트 [(df index, 매도가격), ...]
    수익률 리스트 [(df index, 수익률), ...]
    코스피 수익률 리스트 [(df index, 코스피 수익률), ...]
    누적 수익률
    DataFrame
    """
    code = kwargs['code']
    fromDate = kwargs['fromDate']
    toDate = kwargs['toDate']
    buy_strat = kwargs['buy_strat']
    K_val = kwargs['K_val']
    sell_strat = kwargs['sell_strat']
    spillage = kwargs['spillage']

    """
    Load DataFrame (OHLCV)
    Get Unit-Bid-Price
    Load KOSPI DataFrame (OHLCV)
    """
    df = stock.get_etf_ohlcv_by_date(fromDate, toDate, code)
    # unit_bid = get_unit_bid_price(code)
    unit_bid = 5
    kospi_df = stock.get_index_ohlcv_by_date(fromDate, toDate, "1001")

    """
    Returns
    buy_list: 매수 리스트
    [(i, 매수가1), ...]
    sell_list: 매도 리스트
    [(i, 매도가1), ...]
    yield_list: 수익률 리스트
    [(i, 수익률1), ...]
    kospi_yield_list: 코스피 수익률 리스트
    [(i, 코스피 수익률1), ...]
    culmulative_yield: 누적 수익률
    """
    buy_list = []
    sell_list = []
    yield_list = []
    kospi_yield_list = []
    culmulative_yield = 1

    """
    매수 전략
    """
    if buy_strat == '변동성돌파':
        for i in range(1, len(df) - 1):
            yesterday_high = df.iloc[i-1]['고가']
            yesterday_low = df.iloc[i-1]['저가']
            yesterday_sweep = yesterday_high - yesterday_low
            target_price = df.iloc[i]['시가'] + yesterday_sweep * K_val
            # 매수 가격 발생 여부 확인
            if df.iloc[i]['저가'] < target_price < df.iloc[i]['고가']:
                if target_price % unit_bid == 0:
                    buy_price = target_price + unit_bid * spillage
                else:
                    buy_price = (target_price + unit_bid) // unit_bid * unit_bid + unit_bid * spillage
                buy_list.append((i, buy_price))

    """
    매도 전략
    """
    if sell_strat == '당일종가':
        for buy_pnt in buy_list:
            sell_list.append((buy_pnt[0], df.iloc[buy_pnt[0]]['종가']))
        # 수익률
        for i in range(len(buy_list)):
            delta = (0.99985 * sell_list[i][1] - 1.00015 * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    elif sell_strat == '익일시가':
        for buy_pnt in buy_list:
            sell_list.append((buy_pnt[0] + 1, df.iloc[buy_pnt[0] + 1]['시가']))
        # 수익률
        for i in range(len(buy_list)):
            delta = (0.99985 * sell_list[i][1] - 1.00015 * buy_list[i][1]) / buy_list[i][1]
            yield_list.append((buy_list[i][0], delta))
            culmulative_yield = culmulative_yield * (1 + delta)

    """
    코스피 수익률
    """
    for buy_pnt in buy_list:
        kospi_delta = (kospi_df.iloc[buy_pnt[0]]['종가'] - kospi_df.iloc[buy_pnt[0]]['시가']) / kospi_df.iloc[buy_pnt[0]]['시가']
        kospi_yield_list.append((buy_pnt[0], (1 + kospi_delta)))

    return buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df

def calc_yield_dist(**kwargs):
    """
    :param kwargs:
    code: 종목 코드
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    :return:
    개별 종목 수익률의 기초 통계량 산출 및 Plot
    """
    buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**kwargs)
    _yield_list = []
    for i in range(len(yield_list)):
        _yield_list[i] = yield_list[i][1] * 100
    print('AVG: ', np.mean(_yield_list))
    print('STD: ', np.std(_yield_list))
    print('Max: ', np.max(_yield_list))
    print('Min: ', np.min(_yield_list))
    plt.hist(_yield_list, bins=100, range=(np.min(_yield_list), np.max(_yield_list)), color='r', edgecolor='black', linewidth=1.2)
    plt.xlabel('Yield')
    plt.xticks(np.arange(np.min(_yield_list), np.max(_yield_list), 0.5))
    plt.rc('axes', unicode_minus=False)
    plt.show()

def simulate_invest(**kwargs):
    """
    :param kwargs:
    code_list: 종목 코드 리스트
    fromDate: 시작일
    toDate: 종료일
    buy_start: '변동성돌파'
    K_val = 변동성 돌파 전략의 K 값
    sell_start: '당일종가', '익일시가'
    spillage: 스필리지 (e.g. x: x호가 단위 만큼 매수 spillage 발생)
    :return:
    - 일 평균 전략 수익률 분포
    - 일 평균 매수 횟수 분포
    """
    all_yield_list = []
    code_list = kwargs['code_list']
    for code in code_list:
        param_dict = kwargs
        param_dict['code'] = code
        _, _, yield_list, _, _, _ = calc_yield(**param_dict)
        all_yield_list.extend(yield_list)
    all_yield_list.sort(key=lambda x: x[0])
    max_idx = all_yield_list[-1][0]

    arr = []
    for i in range(max_idx+1):
        arr.append([])
    for yield_tuple in all_yield_list:
        arr[yield_tuple[0]].append(yield_tuple[1]*100)

    daily_count_list = []
    daily_yield_avg_list = []
    for i in range(1, max_idx):
        daily_count_list.append(len(arr[i]))
        if len(arr[i]) != 0:
            daily_yield_avg_list.append(np.mean(arr[i]))

    print('* 일 평균 전략 수익률 기초 통계랑 *')
    print('AVG: ', np.mean(daily_yield_avg_list))
    print('STD: ', np.std(daily_yield_avg_list))
    print('MAX: ', np.max(daily_yield_avg_list))
    print('MIN: ', np.min(daily_yield_avg_list))
    print('================================')
    print('* 일 평균 매수 종목 갯수 기초 통계랑 *')
    print('AVG: ', np.mean(daily_count_list))
    print('STD: ', np.std(daily_count_list))
    print('MAX: ', np.max(daily_count_list))
    print('MIN: ', np.min(daily_count_list))
    print('================================')


# code = code_list[0]
# param_dict = dict({
#     'code': code,
#     'fromDate': '20160601',
#     'toDate': '20210530',
#     'buy_strat': '변동성돌파',
#     'K_val': 0.3,
#     'sell_strat': '당일종가',
#     'spillage': 1, })
# buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**param_dict)

# param_dict = dict({
#     'code_list': code_list,
#     'fromDate': '20160601',
#     'toDate': '20210530',
#     'buy_strat': '변동성돌파',
#     'K_val': 0.3,
#     'sell_strat': '당일종가',
#     'spillage': 1, })
# simulate_invest(**param_dict)

culmulative_yield_list = []
for code in code_list:
    param_dict = dict({
        'code': code,
        'fromDate': '20160601',
        'toDate': '20210530',
        'buy_strat': '변동성돌파',
        'K_val': 0.3,
        'sell_strat': '당일종가',
        'spillage': 1, })
    buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**param_dict)
    culmulative_yield_list.append(culmulative_yield)
print(np.mean(culmulative_yield_list))
culmulative_yield_list = []
for code in code_list:
    param_dict = dict({
        'code': code,
        'fromDate': '20160601',
        'toDate': '20210530',
        'buy_strat': '변동성돌파',
        'K_val': 0.3,
        'sell_strat': '당일종가',
        'spillage': 2, })
    buy_list, sell_list, yield_list, kospi_yield_list, culmulative_yield, df = calc_yield(**param_dict)
    culmulative_yield_list.append(culmulative_yield)
print(np.mean(culmulative_yield_list))
