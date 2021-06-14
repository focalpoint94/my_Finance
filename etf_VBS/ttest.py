import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from pykrx import stock

def get_unit_bid_price(code):
    opt = webdriver.ChromeOptions()
    opt.add_argument('headless')

    drv = webdriver.Chrome('./chromedriver.exe', options=opt)
    drv.implicitly_wait(3)
    base_url = 'https://finance.naver.com/item/sise.nhn?code='
    code = str(code)
    drv.get(base_url+code)

    bs = BeautifulSoup(drv.page_source, 'lxml')
    drv.quit()

    temp = bs.find_all('table', class_='type2')[1]
    sub_temp = temp.find_all('span', class_='tah p11 nv01')

    return int(sub_temp[1].get_text().strip().replace(',', '')) - int(sub_temp[3].get_text().strip().replace(',', ''))

def get_ETF_list(num_ETF=50):
    df = pd.read_csv('ETFs.txt')
    code_list = list(df['codes'])
    code_list = code_list[:num_ETF]

    return code_list

print(get_ETF_list())