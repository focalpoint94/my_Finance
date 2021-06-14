from bs4 import BeautifulSoup

from selenium import webdriver
import pandas as pd


def get_ETF_list(num_ETF=25):
    opt = webdriver.ChromeOptions()
    opt.add_argument('headless')
    drv = webdriver.Chrome('./chromedriver.exe', options=opt)
    drv.implicitly_wait(3)
    drv.get('https://finance.naver.com/sise/etf.nhn')

    bs = BeautifulSoup(drv.page_source, 'lxml')
    drv.quit()

    # df: 거래량 기준 모든 ETF
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
    for i in range(len(df)):
        name = df.iloc[i]['종목명']
        company_names.append(name)
        codes.append(etfs[name])
    df.insert(1, 'code', codes)

    df_index = []
    for idx in range(len(df)):
        if "단기" in df.iloc[idx]['종목명']:
            df_index.append(df.index[idx])
    df = df.drop(index=df_index, axis=0)

    code_list = list(df['code'][:num_ETF])
    for i in range(len(code_list)):
        code_list[i] = 'A' + code_list[i]

    name_list = list(df['종목명'][:num_ETF])

    return code_list, name_list


code_list, name_list = get_ETF_list(num_ETF=30)
data = {'codes': code_list, 'company': name_list}

df = pd.DataFrame(data=data)
df.to_csv('ETFs.txt', index=False)

