
"""
get_all_financial_data.py
company_info.xlsx 파일로부터 공시 기업 목록을 불러와서
특정 기간부터의 재무 데이터를 fsdata 폴더에 저장
"""

import dart_fss as dart
import pandas as pd
from time import sleep
from datetime import datetime, timedelta


def print_log(message):
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)


def _get_all_financial_data(start_year: int=2009, start_idx: int=0):
    """
    :param start_year: 재무제표표 시작 연도
    :return: 재무제표 Excel File
    """

    """
    API Key
    """
    api_key = '423358f7b1762af4cf81bb633c44244636f9037c'
    dart.set_api_key(api_key=api_key)

    """
    Load Company_info.xlsx
    """
    df = pd.read_excel('company_info.xlsx', index_col=1, engine='openpyxl')
    df.index = df.index.map('{:08d}'.format)
    df['Stock Code'] = df['Stock Code'].map('{:06d}'.format)
    df = df[['Name', 'Stock Code', 'Last Date']]

    """
    Get & Save Data
    """
    for i in range(start_idx, len(df)):
        corp_code = df.index[i]
        stock_code = df.iloc[i]['Stock Code']
        try:
            try:
                fs = dart.fs.extract(corp_code=corp_code, bgn_de=str(start_year)+'0101')
                fs.save(filename=stock_code+'.xlsx')
            except:
                fs = dart.fs.extract(corp_code=corp_code, separate=True, bgn_de="2009" + '0101')
                fs.save(filename=stock_code + '.xlsx')
            print_log('* ' + df.iloc[i]['Name'] + ' 재무 데이터 다운로드 완료 (' + str(round(i / len(df) * 100, 2)) + '%)')
        except Exception as ex:
            print(str(ex))
        if (i + 1) % (start_idx + 2000) == 0:
            print_log('* API 사용 제한에 따른 휴식')
            tm_now = datetime.now()
            tm_next = datetime.now() + timedelta(days=1)
            tm_next = tm_next.replace(hour=0, minute=5, second=0, microsecond=0)
            delta = (tm_next - tm_now).seconds
            sleep(delta)
    print_log('* Completed')


if __name__ == '__main__':
    _get_all_financial_data(start_idx=0)


