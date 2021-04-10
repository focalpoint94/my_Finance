# Naver에서 거래량 상위 100개 ETF 목록 가져오기

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd

opt = webdriver.ChromeOptions()
opt.add_argument('headless')

drv = webdriver.Chrome('./chromedriver.exe', options=opt)
drv.implicitly_wait(3)
drv.get('https://finance.naver.com/sise/etf.nhn')

bs = BeautifulSoup(drv.page_source, 'lxml')
drv.quit()

table = bs.find_all('table', class_='type_1 type_etf')
df = pd.read_html(str(table), header=0)[0]
df = df.drop(columns=['Unnamed: 9'])
df = df.dropna()
df = df.sort_values(by='거래량', ascending=False)

etf_td = bs.find_all('td', class_='ctg')
etfs = {}
for td in etf_td:
    s = str(td.a['href']).split('=')
    code = s[-1]
    etfs[td.a.text] = code

company_names = []
codes = []
for i in range(100):
    name = df.iloc[i]['종목명']
    company_names.append(name)
    codes.append(etfs[name])

data = {'company': company_names, 'code': codes}
dx = pd.DataFrame(data=data)
dx.to_csv('ETFs.txt', index=False)


