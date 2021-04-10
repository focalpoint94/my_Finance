from time import sleep
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import urllib.parse as urlparse

class my_stock_Timer:
    def sleep_after_market(self):
        tmnow = datetime.now()
        tmnext = datetime.now()
        tmnext = tmnext + timedelta(days=1)
        tmnext = tmnext.replace(hour=9, minute=5, second=0, microsecond=0)
        delta = tmnext - tmnow
        delta = delta.seconds
        sleep(delta)

    def sleep_after_market_until_hour(self, hour):
        tmnow = datetime.now()
        tmnext = datetime.now()
        tmnext = tmnext + timedelta(days=1)
        tmnext = tmnext.replace(hour=hour, minute=0, second=0, microsecond=0)
        delta = tmnext - tmnow
        delta = delta.seconds
        sleep(delta)

    def is_Holiday(self, date):
        # date: datetime.now()
        # 토요일 or 일요일 check
        if date.weekday() >= 5:
            return True
        # 국경일 or 공휴일 check
        URL = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService'
        OPERATION = 'getHoliDeInfo'  # 국경일 + 공휴일 정보 조회 오퍼레이션
        SERVICEKEY = 'fOVn1oXvPpN1SWpW1SV0Tai%2FCzVEWhXD6MYrt3HZlNhyf1AnlH5NdZtCVznI8Lf2OUpfUJ4HB068SRfXDRB8%2Fg%3D%3D'
        solYear = str(date.year)
        solMonth = str(format(date.month, '02'))
        params = {'solYear': solYear, 'solMonth': solMonth}
        params = urlparse.urlencode(params)
        request_query = URL + '/' + OPERATION + '?' + params + '&' + 'serviceKey' + '=' + SERVICEKEY
        response = requests.get(url=request_query)
        holidays = []
        if True == response.ok:
            html = BeautifulSoup(response.text, "lxml")
            temp = html.find_all("locdate")
            for x in temp:
                holidays.append(x.text)
        date = date.strftime('%Y%m%d')
        if date in holidays:
            return True
        return False
