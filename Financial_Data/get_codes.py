

"""
get_codes.py
2009년 ~ 2021년 상장 회사 종목 코드 저장
"""

from pykrx import stock
from time import sleep
import json

"""
Params
"""
start_year = 2009
end_year = 2021

"""
Get Codes
"""
code_set = set([])
for ref_year in range(start_year, end_year+1):
    ref_date = str(ref_year) + "0101"
    tickers1 = stock.get_market_ticker_list(ref_date, market="KOSPI")
    code_set.update(tickers1)
    sleep(5)
    tickers2 = stock.get_market_ticker_list(ref_date, market="KOSDAQ")
    code_set.update(tickers2)
    sleep(5)
code_list = list(code_set)

"""
Save as code_list.json
"""
with open('krx_codes.json', 'w') as f:
    json.dump(code_list, f)

"""
Check code_list.json File (only for debug)
"""
# with open('krx_codes.json', 'r') as f:
#     y = json.load(f)
#     print(y)

