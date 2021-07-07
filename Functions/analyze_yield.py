"""
analyze_yield.py
Input: List
[(date1, [yield list1]), (date2, [yield list2]), ...]
date: "20210602" (str)
yield list: [0.002, 0.332, -0.12, ...]
Output
1. Statistics
투자 기간
일 평균 수익률
누적수익률
CAGR
승률
MAD
2. Chart
일 평균 수익률 분포
누적 수익률 차트
월간 수익률 차트
"""
import numpy as np
import os
import matplotlib.pyplot as plt
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from time import sleep
import math
from random import randint
import matplotlib.dates as mdates
import json
import FinanceDataReader as fdr



def _analyze_yield(yield_list):
    """
    :param yield_list: List
    [(date1, [yield list1]), (date2, [yield list2]), ...]
    date: "20210602" (str)
    yield list: [0.002, 0.332, -0.12, ...]
    :return:
    Output
    1. Statistics
    투자 기간: investment_period
    일 평균 수익률: average_daily_yield
    누적수익률: culmulative_yield
    MAD: MDD
    CAGR: CAGR
    승률: win_rate
    2. Chart
    일 평균 수익률 분포
    누적 수익률 차트
    월간 수익률 차트
    """
    """
    Graph Directory
    """
    graph_dir = './graphs/'
    if not os.path.isdir(graph_dir):
        os.mkdir(graph_dir)

    """
    투자 기간
    """
    investment_period = yield_list[0][0] + ' ~ ' + yield_list[-1][0]
    investment_td = datetime.strptime(yield_list[-1][0], "%Y%m%d") - datetime.strptime(yield_list[0][0], "%Y%m%d")
    investment_td_yr = investment_td / timedelta(days=365)

    """
    일 평균 수익률
    """
    average_yield_list = [(item[0], np.mean(item[1])) for item in yield_list]
    _average_yield_list = [item[1] for item in average_yield_list]
    average_daily_yield = np.mean(_average_yield_list)

    """
    일 평균 수익률 분포
    """
    figure1 = plt.figure(1, figsize=(9, 9))
    plt.hist(_average_yield_list, bins=100, color='black', edgecolor='black',
             linewidth=1.2)
    plt.xlabel('일 평균 수익률')
    plt.rc('axes', unicode_minus=False)
    plt.xticks(np.arange(1.1*np.min(_average_yield_list), 1.1*np.max(_average_yield_list), 0.2))
    figure1.savefig(fname=graph_dir + '일 평균 수익률', dpi=300)
    plt.close()

    """
    누적 수익률
    """
    culmulative_yield_list = []
    culmulative_yield = 1
    for i, item in enumerate(average_yield_list):
        culmulative_yield = culmulative_yield * (1 + item[1]/100)
        culmulative_yield_list.append((item[0], culmulative_yield))

    """
    CAGR
    """
    CAGR = math.pow(culmulative_yield, 1/investment_td_yr) - 1

    """
    MDD
    """
    culmulative_highest_yield_list = []
    culmulative_highest_yield_list.append(culmulative_yield_list[0])
    for i in range(1, len(culmulative_yield_list)):
        if culmulative_yield_list[i][1] > culmulative_highest_yield_list[i-1][1]:
            culmulative_highest_yield_list.append(culmulative_yield_list[i])
        else:
            culmulative_highest_yield_list.append((culmulative_yield_list[i][0], culmulative_highest_yield_list[i-1][1]))
    MDD = 0
    for i in range(len(culmulative_highest_yield_list)):
        MDD = max(MDD, (culmulative_highest_yield_list[i][1] - culmulative_yield_list[i][1]) / culmulative_highest_yield_list[i][1])

    """
    누적 수익률 차트
    """
    date_list = [item[0] for item in culmulative_yield_list]
    for i in range(len(date_list)):
        date_list[i] = datetime.strptime(date_list[i], "%Y%m%d")

    # 전략
    _culmulative_yield_list = [item[1] for item in culmulative_yield_list]

    # KOSPI
    kospi_index_list = []
    start_date = datetime.strftime(date_list[0], "%Y-%m-%d")
    kospi_df = fdr.DataReader('KS11', start_date)
    for date in date_list:
        s_date = datetime.strftime(date, "%Y%m%d")
        kospi_index_list.append([s_date, kospi_df.loc[date]['Close']])
    kospi_base = kospi_index_list[0][1]
    for i in range(len(kospi_index_list)):
        kospi_index_list[i][1] = kospi_index_list[i][1] / kospi_base
    _kospi_index_list = [item[1] for item in kospi_index_list]

    # KOSDAQ
    kosdaq_index_list = []
    start_date = datetime.strftime(date_list[0], "%Y-%m-%d")
    kosdaq_df = fdr.DataReader('KQ11', start_date)
    for date in date_list:
        s_date = datetime.strftime(date, "%Y%m%d")
        kosdaq_index_list.append([s_date, kosdaq_df.loc[date]['Close']])
    kosdaq_base = kosdaq_index_list[0][1]
    for i in range(len(kosdaq_index_list)):
        kosdaq_index_list[i][1] = kosdaq_index_list[i][1] / kosdaq_base
    _kosdaq_index_list = [item[1] for item in kosdaq_index_list]

    figure1 = plt.figure(1, figsize=(9, 9))
    p1 = figure1.add_subplot()
    p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.plot(date_list, _culmulative_yield_list, c='r', label='전략 수익률')
    plt.plot(date_list, _kospi_index_list, c='g', label='KOSPI')
    plt.plot(date_list, _kosdaq_index_list, c='b', label='KOSDAQ')
    plt.legend(loc='best')
    figure1.savefig(fname=graph_dir + '누적 수익률', dpi=300)
    plt.close()

    """
    월간 수익률 차트
    """
    st = datetime.strftime(date_list[0], "%y%m")
    ed = datetime.strftime(date_list[-1], "%y%m")
    start_year = int(st[:2])
    end_year = int(ed[:2])
    start_month = int(st[2:])
    end_month = int(ed[2:])
    if start_year == end_year:
        num_bins = end_month - start_month + 1
    else:
        num_bins = (end_year - start_year - 1) * 12 + (12 - start_month + 1) + end_month
    labels = []
    label = st
    labels.append(label)
    for i in range(num_bins-1):
        if int(label[2:]) == 12:
            label = str(int(label[:2])+1) + "01"
        else:
            label = label[:2] + f"{int(label[2:])+1:02d}"
        labels.append(label)

    monthly_yield_list = [[] for _ in range(num_bins)]
    for item in average_yield_list:
        label = item[0][2:6]
        to_idx = labels.index(label)
        monthly_yield_list[to_idx].append(item[1])
    monthly_yield_list = [np.mean(item) for item in monthly_yield_list]

    new_index_list = []
    for i in range(len(kospi_df)):
        new_index_list.append(datetime.strftime(kospi_df.index[i], "%Y%m%d"))
    kospi_df.index = new_index_list
    new_index_list = []
    for i in range(len(kosdaq_df)):
        new_index_list.append(datetime.strftime(kosdaq_df.index[i], "%Y%m%d"))
    kosdaq_df.index = new_index_list

    monthly_kospi_yield_list = []
    monthly_kosdaq_yield_list = []

    for i in range(num_bins):
        label = labels[i]
        month_idx = []
        for index in kospi_df.index:
            if index[2:6] == label:
                month_idx.append(index)
        start_price = kospi_df.loc[month_idx[0]]['Open']
        end_price = kospi_df.loc[month_idx[-1]]['Close']
        _yield = (end_price - start_price) / start_price
        monthly_kospi_yield_list.append(_yield)
    for i in range(num_bins):
        label = labels[i]
        month_idx = []
        for index in kosdaq_df.index:
            if index[2:6] == label:
                month_idx.append(index)
        start_price = kosdaq_df.loc[month_idx[0]]['Open']
        end_price = kosdaq_df.loc[month_idx[-1]]['Close']
        _yield = (end_price - start_price) / start_price
        monthly_kosdaq_yield_list.append(_yield)

    x = np.arange(len(labels))
    width = 0.15
    figure1, ax = plt.subplots()
    rects1 = ax.bar(x - 0.35, monthly_yield_list, width, color='r', label='전략 수익률')
    rects2 = ax.bar(x, monthly_kospi_yield_list, width, color='g', label='KOSPI')
    rects3 = ax.bar(x + 0.35, monthly_kosdaq_yield_list, width, color='b', label='KOSDAQ')
    ax.set_xlabel('기간')
    ax.set_ylabel('Yield')
    ax.set_title('월간 수익률 차트')
    ax.set_xticks(x)
    plt.xticks(rotation=45)
    ax.set_xticklabels(labels)
    ax.legend()
    figure1.tight_layout()
    figure1.savefig(fname=graph_dir + '월간 수익률', dpi=300)
    plt.close()

    """
    승률
    """
    num_total = 0
    num_win = 0
    for item in yield_list:
        for _yield in item[1]:
            num_total += 1
            if _yield > 0:
                num_win += 1
    win_rate = num_win / num_total

    return investment_period, average_daily_yield, culmulative_yield, MDD, CAGR, win_rate



"""
Input Example
"""
while True:
    try:
        dates_df = stock.get_index_ohlcv_by_date("20190101", "20210705", "1001")
        break
    except json.decoder.JSONDecodeError:
        pass
dates_list = dates_df.index.to_list()
for i, date in enumerate(dates_list):
    dates_list[i] = datetime.strftime(date, "%Y%m%d")
yield_list = []
date = datetime.strptime("20190101", "%Y%m%d")
for i in range(730):
    date = date + timedelta(days=1)
    s_date = datetime.strftime(date, "%Y%m%d")
    if s_date not in dates_list:
        continue
    if i % 50 == 0:
        continue
    num_bought = randint(7, 12)
    day_yield_list = list(np.random.normal(size=num_bought) + 0.2)
    yield_list.append((datetime.strftime(date, "%Y%m%d"), day_yield_list))


investment_period, average_daily_yield, culmulative_yield, MDD, CAGR, win_rate = _analyze_yield(yield_list)
print(investment_period, average_daily_yield, culmulative_yield, MDD, CAGR, win_rate)


