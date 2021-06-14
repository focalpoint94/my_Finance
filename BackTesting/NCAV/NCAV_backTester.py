

from pykrx import stock
import pandas as pd
import numpy as np
import OpenDartReader
import math
from time import sleep

def NCAV_backTester(start_year: int):
    """
    :param start_year: test start year (e.g. 2015)
    """
    """
    Dart API
    """
    api_key = '423358f7b1762af4cf81bb633c44244636f9037c'
    dart = OpenDartReader(api_key)

    term_list = []
    y1_list = []
    y2_list = []

    for year in range(start_year, 2021):
        year = str(year)
        stock_basket = []
        """
        시가총액
        """
        date = year + "0101"
        df = stock.get_market_cap_by_ticker(date)
        df = df[['시가총액']]

        for code in df.index.to_list():
            sleep(1)
            """
            재무 정보 없는 경우 pass
            """
            try:
                temp = dart.finstate(code, year)
                fs_xfs = temp[temp['fs_div'].str.contains('CFS')]
                if fs_xfs.empty:
                    fs_xfs = temp[temp['fs_div'].str.contains('OFS')]

                """
                유동자산, 총부채
                """
                fs_bs = fs_xfs[fs_xfs['sj_div'].str.contains('BS')]
                fs_la = fs_bs[fs_bs['account_nm'].str.contains('유동자산')]
                fs_debt = fs_bs[fs_bs['account_nm'].str.contains('부채총계')]
                liquid_asset = int(fs_la[['thstrm_amount']].iloc[0, 0].replace(',', '').strip())
                debt = int(fs_debt[['thstrm_amount']].iloc[0, 0].replace(',', '').strip())

                """
                세후이익
                """
                temp = dart.finstate(code, year)
                fs_is = fs_xfs[fs_xfs['sj_div'].str.contains('IS')]
                fs_np = fs_is[fs_is['account_nm'].str.contains('당기순이익')]
                net_profit = int(fs_np[['thstrm_amount']].iloc[0, 0].replace(',', '').strip())

            except:
                continue

            """
            Stock Basket
            Conditions
            1) 유동자산 - 총부채 > 시가총액 * 1.5
            2) 세후이익 > 0
            """
            if liquid_asset - debt > df.loc[code]['시가총액'] * 1.5 and net_profit > 0:
                stock_basket.append(code)

        """
        Calculation
        """
        name_list = []
        yield_list = []
        tax_rate = 0.00315
        for code in stock_basket:
            name = stock.get_market_ticker_name(code)
            name_list.append(name)
            temp = stock.get_market_ohlcv_by_date(date, str(int(year) + 1) + "0101", code)
            buy_price = temp.iloc[0]['시가']
            sell_price = temp.iloc[-1]['종가']
            """
            매수 기간 거래 정지 종목 제외
            """
            if buy_price == 0:
                yield_list.append(math.nan)
            yield_with_tax = ((1 - tax_rate) * sell_price - (1 + tax_rate) * buy_price) / buy_price + 1
            yield_list.append(yield_with_tax)
        kospi = stock.get_index_ohlcv_by_date(date, str(int(year) + 1) + "0101", "1001")
        kospi_yield = (kospi.iloc[-1]['종가'] - kospi.iloc[0]['시가']) / kospi.iloc[0]['시가'] + 1

        """
        NAN Check
        """
        _yield_list = [_yield for _yield in yield_list if not math.isnan(_yield)]

        """
        Results
        """
        print("* NCAV 전략")
        print("* 기간: " + year + " ~ " + str(int(year)+1))
        print("* 종목: ", stock_basket)
        print("* 종목명: ", name_list)
        print("* 수익률: ", yield_list)
        print("* 평균 수익률: ", round(np.mean(_yield_list), 4))
        print("* 동기간 코스피 수익률: ", round(kospi_yield, 4))

        term_list.append(year + " ~ " + str(int(year)+1))
        y1_list.append(round(np.mean(_yield_list), 4))
        y2_list.append(round(kospi_yield, 4))

    data = {'Term': term_list, '전략 수익률': y1_list, '동기간 코스피 수익률': y2_list}
    df = pd.DataFrame(data=data)
    writer = pd.ExcelWriter('./results.xlsx', engine='xlsxwriter')
    df.to_excel(writer)
    writer.close()


NCAV_backTester(2015)




# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(fs_is)



