# etf_VBS.py
import requests
import json
import os, sys, ctypes
import win32com.client
import pandas as pd
from datetime import datetime
import time, calendar
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver


# 크레온 플러스 공통 OBJECT
cpCodeMgr = win32com.client.Dispatch('CpUtil.CpStockCode')
cpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil')
cpStock = win32com.client.Dispatch('DsCbo1.StockMst')
cpOhlc = win32com.client.Dispatch('CpSysDib.StockChart')
cpBalance = win32com.client.Dispatch('CpTrade.CpTd6033')
cpCash = win32com.client.Dispatch('CpTrade.CpTdNew5331A')
cpOrder = win32com.client.Dispatch('CpTrade.CpTd0311')


# 1. Creon System Check
def check_creon_system():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('check_creon_system() : admin user -> Failed')
        return False

    if (cpStatus.IsConnect == 0):
        print('check_creon_system() : connect to server -> Failed')
        return False

    if (cpTradeUtil.TradeInit(0) != 0):
        print('check_creon_system(): init trade -> Failed')
        return False

    return True


# 2. Logs (Slack, Shell)
def post_message(slack_data):
    # channel: creon-logs
    webhook_url = "https://hooks.slack.com/services/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"
    response = requests.post(webhook_url, data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text))


def dbgout(message):
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S]') + message
    slack_data = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": strbuf,
                    "emoji": True
                }
            }
        ]
    }
    post_message(slack_data)


def printlog(message, *args):
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)


# 3. 주가 및 계좌 정보 조회
def get_current_price(code):
    cpStock.SetInputValue(0, code)
    cpStock.BlockRequest()

    item = {}
    item['cur_price'] = cpStock.GetHeaderValue(11)
    item['ask'] = cpStock.GetHeaderValue(16)
    item['bid'] = cpStock.GetHeaderValue(17)

    return item['cur_price'], item['ask'], item['bid']


# 4. OHLC
"""
"CpSysDib.StockChart" API
https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=102&page=1&searchString=CpSysDib.StockChart&p=8841&v=8643&m=9505
"""
cpOhlc = win32com.client.Dispatch("CpSysDib.StockChart")

def get_ohlc(code, qty):
    cpOhlc.SetInputValue(0, code)
    cpOhlc.SetInputValue(1, ord('2'))
    cpOhlc.SetInputValue(4, qty)
    cpOhlc.SetInputValue(5, [0, 2, 3, 4, 5])
    cpOhlc.SetInputValue(6, ord('D'))
    cpOhlc.SetInputValue(9, ord('1'))
    cpOhlc.BlockRequest()

    count = cpOhlc.GetHeaderValue(3)
    columns = ['open', 'high', 'low', 'close']
    index = []
    rows = []

    for i in range(count):
        index.append(cpOhlc.GetDataValue(0, i))
        rows.append([cpOhlc.GetDataValue(1, i), cpOhlc.GetDataValue(2, i),
                     cpOhlc.GetDataValue(3, i), cpOhlc.GetDataValue(4, i)])

    df = pd.DataFrame(rows, columns=columns, index=index)
    return df


# 5. 계좌 조회
"""
CpTrade.CpTd6033 API
https://money2.creontrade.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_Read_Page.aspx?boardseq=284&seq=176&page=1&searchString=CpTrade.CpTd6033&p=8841&v=8643&m=9505
"""

def get_stock_balance(code):
    """인자로 받은 종목의 종목명과 수량을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpBalance.SetInputValue(0, acc)         # 계좌번호
    cpBalance.SetInputValue(1, accFlag[0])  # 상품구분 - 주식 상품 중 첫번째
    cpBalance.SetInputValue(2, 50)          # 요청 건수(최대 50)
    cpBalance.BlockRequest()
    if code == 'ALL':
        dbgout('계좌명: ' + str(cpBalance.GetHeaderValue(0)))
        dbgout('결제잔고수량 : ' + str(cpBalance.GetHeaderValue(1)))
        dbgout('평가금액: ' + str(cpBalance.GetHeaderValue(3)))
        dbgout('평가손익: ' + str(cpBalance.GetHeaderValue(4)))
        dbgout('종목수: ' + str(cpBalance.GetHeaderValue(7)))
    stocks = []
    for i in range(cpBalance.GetHeaderValue(7)):
        stock_code = cpBalance.GetDataValue(12, i)  # 종목코드
        stock_name = cpBalance.GetDataValue(0, i)   # 종목명
        stock_qty = cpBalance.GetDataValue(15, i)   # 수량
        if code == 'ALL':
            dbgout(str(i+1) + ' ' + stock_code + '(' + stock_name + ')'
                + ':' + str(stock_qty))
            stocks.append({'code': stock_code, 'name': stock_name,
                'qty': stock_qty})
        if stock_code == code:
            return stock_name, stock_qty
    if code == 'ALL':
        return stocks
    else:
        stock_name = cpCodeMgr.CodeToName(code)
        return stock_name, 0


# 6. 주문 가능 금액 조회
def get_current_cash():
    """증거금 100% 주문 가능 금액을 반환한다."""
    cpTradeUtil.TradeInit()
    acc = cpTradeUtil.AccountNumber[0]    # 계좌번호
    accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체, 1:주식, 2:선물/옵션
    cpCash.SetInputValue(0, acc)              # 계좌번호
    cpCash.SetInputValue(1, accFlag[0])      # 상품구분 - 주식 상품 중 첫번째
    cpCash.BlockRequest()
    return cpCash.GetHeaderValue(9) # 증거금 100% 주문 가능 금액


# 7. 거래량 상위 N개 ETF 가져오기
def get_ETF_list(num_ETF=30):
    df = pd.read_csv('ETFs.txt')
    code_list = list(df['codes'])
    if len(code_list) > num_ETF:
        code_list = code_list[:num_ETF]
    return code_list


# 8. Target Price 계산
def get_target_price(code):
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5
        return target_price
    except Exception as ex:
        dbgout("'get_target_price() -> exception! " + str(ex) + "'")
        return None


# 9. Moving Average 계산
def get_movingaverage(code, window):
    """인자로 받은 종목에 대한 이동평균가격을 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(code, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()
        ma = closes.rolling(window=window).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout('get_movingavrg(' + str(window) + ') -> exception! ' + str(ex))
        return None


# 10. 매수 함수
def buy_etf(code):
    """인자로 받은 종목을 최우선 지정가 FOK 조건으로 매수한다."""
    try:
        global bought_list      # 함수 내에서 값 변경을 하기 위해 global로 지정
        if code in bought_list: # 매수 완료 종목이면 더 이상 안 사도록 함수 종료
            #printlog('code:', code, 'in', bought_list)
            return False
        time_now = datetime.now()
        current_price, ask_price, bid_price = get_current_price(code)
        target_price = get_target_price(code)    # 매수 목표가
        # ma5_price = get_movingaverage(code, 5)   # 5일 이동평균가
        # ma10_price = get_movingaverage(code, 10) # 10일 이동평균가
        buy_qty = 0        # 매수할 수량 초기화
        if ask_price > 0:  # 매수호가가 존재하면
            buy_qty = buy_amount // ask_price
        stock_name, stock_qty = get_stock_balance(code)  # 종목명과 보유수량 조회
        # print('current_price: ', current_price, 'target_price: ', target_price,
        #       'ma5_price: ', ma5_price, 'ma10_price: ', ma10_price)
        # printlog('bought_list:', bought_list, 'len(bought_list):',
        #    len(bought_list), 'target_buy_count:', target_buy_count)
        if current_price > target_price:
            printlog(stock_name + '(' + str(code) + ') ' + str(buy_qty) +
                'EA : ' + str(current_price) + ' meets the buy condition!`')
            cpTradeUtil.TradeInit()
            acc = cpTradeUtil.AccountNumber[0]      # 계좌번호
            accFlag = cpTradeUtil.GoodsList(acc, 1) # -1:전체,1:주식,2:선물/옵션
            # 최유리 IOC 매수 주문 설정
            cpOrder.SetInputValue(0, "2")        # 2: 매수
            cpOrder.SetInputValue(1, acc)        # 계좌번호
            cpOrder.SetInputValue(2, accFlag[0]) # 상품구분 - 주식 상품 중 첫번째
            cpOrder.SetInputValue(3, code)       # 종목코드
            cpOrder.SetInputValue(4, buy_qty)    # 매수할 수량
            cpOrder.SetInputValue(5, ask_price)  # 매수 희망 가격
            cpOrder.SetInputValue(7, "0")        # 주문조건 0:기본, 1:IOC, 2:FOK
            cpOrder.SetInputValue(8, "01")       # 주문호가 01:보통, 03:시장가
                                                 # 5:조건부, 12:최유리, 13:최우선
            # 매수 주문 요청
            ret = cpOrder.BlockRequest()
            printlog('최유리 IOC 매수 ->', stock_name, code, buy_qty, '->', ret)
            if ret != 0:
                printlog('주문 오류.')
                return False
            if ret == 4:
                remain_time = cpStatus.LimitRequestRemainTime
                printlog('주의: 연속 주문 제한에 걸림. 대기 시간:', remain_time/1000)
                time.sleep(remain_time/1000)
                return False
            rqStatus = cpOrder.GetDibStatus()
            errMsg = cpOrder.GetDibMsg1()
            if rqStatus != 0:
                printlog("주문 실패: ", rqStatus, errMsg)
            time.sleep(2)
            printlog('현금주문 가능금액 :', buy_amount)
            stock_name, bought_qty = get_stock_balance(code)
            printlog('get_stock_balance :', stock_name, stock_qty)
            if bought_qty > 0:
                bought_list.append(code)
                dbgout("`buy_etf("+ str(stock_name) + ' : ' + str(code) +
                    ") -> " + str(bought_qty) + "EA bought!" + "`" + "(Target Price: " + str(target_price) + ")")
    except Exception as ex:
        dbgout("`buy_etf("+ str(code) + ") -> exception! " + str(ex) + "`")


# 11. 매도 함수
def sell_all():
    """보유한 모든 종목을 최유리 지정가 IOC 조건으로 매도한다."""
    try:
        cpTradeUtil.TradeInit()
        acc = cpTradeUtil.AccountNumber[0]       # 계좌번호
        accFlag = cpTradeUtil.GoodsList(acc, 1)  # -1:전체, 1:주식, 2:선물/옵션
        while True:
            stocks = get_stock_balance('ALL')
            total_qty = 0
            for s in stocks:
                total_qty += s['qty']
            if total_qty == 0:
                return True
            for s in stocks:
                if s['qty'] != 0:
                    cpOrder.SetInputValue(0, "1")         # 1:매도, 2:매수
                    cpOrder.SetInputValue(1, acc)         # 계좌번호
                    cpOrder.SetInputValue(2, accFlag[0])  # 주식상품 중 첫번째
                    cpOrder.SetInputValue(3, s['code'])   # 종목코드
                    cpOrder.SetInputValue(4, s['qty'])    # 매도수량
                    cpOrder.SetInputValue(7, "1")   # 조건 0:기본, 1:IOC, 2:FOK
                    cpOrder.SetInputValue(8, "12")  # 호가 12:최유리, 13:최우선
                    # 최유리 IOC 매도 주문 요청
                    ret = cpOrder.BlockRequest()
                    printlog('최유리 IOC 매도', s['code'], s['qty'],
                        '-> cpOrder.BlockRequest() -> returned', ret)
                    if ret == 4:
                        remain_time = cpStatus.LimitRequestRemainTime
                        printlog('주의: 연속 주문 제한, 대기시간:', remain_time/1000)
                    rqStatus = cpOrder.GetDibStatus()
                    errMsg = cpOrder.GetDibMsg1()
                    if rqStatus != 0:
                        printlog("주문 실패: ", rqStatus, errMsg)
                time.sleep(1)
            time.sleep(30)
    except Exception as ex:
        dbgout("sell_all() -> exception! " + str(ex))


# 12. Main
if __name__ == '__main__':
    try:
        symbol_list = get_ETF_list()
        # symbol_list = ['A122630', 'A252670', 'A233740', 'A250780', 'A225130',
        #      'A280940', 'A261220', 'A217770', 'A295000', 'A176950']
        bought_list = []     # 매수 완료된 종목 리스트
        target_buy_count = 10 # 매수할 종목 수
        buy_percent = 1 / 10 * 0.95
        printlog('check_creon_system() :', check_creon_system())  # 크레온 접속 점검
        stocks = get_stock_balance('ALL')      # 보유한 모든 종목 조회
        total_cash = int(get_current_cash())   # 100% 증거금 주문 가능 금액 조회
        buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
        printlog('100% 증거금 주문 가능 금액 :', total_cash)
        printlog('종목별 주문 비율 :', buy_percent)
        printlog('종목별 주문 금액 :', buy_amount)
        printlog('시작 시간 :', datetime.now().strftime('%m/%d %H:%M:%S'))
        soldout = False

        while True:
            t_now = datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_end = t_now.replace(hour=14, minute=30, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=10, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
            today = datetime.today().weekday()
            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                printlog('Today is', 'Saturday.' if today == 5 else 'Sunday.')
                sys.exit(0)
            if t_9 < t_now < t_start and soldout == False:
                soldout = True
                sell_all()
            if t_start < t_now < t_end:  # AM 09:05 ~ PM 02:00 : 매수
                for sym in symbol_list:
                    if len(bought_list) < target_buy_count:
                        buy_etf(sym)
                        time.sleep(1)
                if t_now.minute == 30 and 0 <= t_now.second <= 5:
                    get_stock_balance('ALL')
                    time.sleep(5)
            if t_sell < t_now < t_exit:  # PM 03:00 ~ PM 03:20 : 모두 매도
                if sell_all() == True:
                    dbgout('`sell_all() returned True -> self-destructed!`')
                    sys.exit(0)
            if t_exit < t_now:  # PM 03:20 ~ : 프로그램 종료
                dbgout('`self-destructed!`')
                sys.exit(0)
            time.sleep(3)
    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')

