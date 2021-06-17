
"""
get_company_info.py
Dart 공시 주식회사 Info Excel File 생성
"""
import dart_fss as dart
import pandas as pd
import json

"""
API Key
"""
api_key = '****************************************'
dart.set_api_key(api_key=api_key)

"""
상장 회사 종목 코드 가져오기 (2009 - 2021)
"""
with open('krx_codes.json', 'r') as f:
    krx_codes = json.load(f)

"""
공시 기업 정리
"""
data = dart.api.filings.get_corp_code()
corp_code_list = []
corp_name_list = []
stock_code_list= []
modify_date_list = []
dart_company_info_list = [corp_code_list, corp_name_list, stock_code_list, modify_date_list]
for i in range(len(data)):
    temp_list = []
    for key, val in data[i].items():
        temp_list.append(val)
    if temp_list[2] is None or temp_list[2] not in krx_codes:
        continue
    for j, temp in enumerate(temp_list):
        dart_company_info_list[j].append(temp)
data = {'Code': corp_code_list, 'Name': corp_name_list, 'Stock Code': stock_code_list, 'Last Date': modify_date_list}
df = pd.DataFrame(data=data)
writer = pd.ExcelWriter('./company_info.xlsx', engine='xlsxwriter')
df.to_excel(writer)
writer.close()
