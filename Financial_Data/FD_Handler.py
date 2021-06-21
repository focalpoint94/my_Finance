
"""
FD_Handler.py
* 사용 예시 *
FDH = FD_Handler(code='000060')
all_list = FDH.get_data(type='all')
print(all_list)
label_list = ['당기순이익', '계속영업이익']
inc_kw_list = []
exc_kw_list = ['귀속']
k, v = FDH.get_value(year='2015', label_list=label_list, inc_kw_list=inc_kw_list, exc_kw_list=exc_kw_list)
print(k, v)

=======================================
유효한 조합 List
=======================================
* 당기순이익 *
label_list = ['당기순이익', '계속영업이익']
inc_kw_list = []
exc_kw_list = ['귀속']

* 영업활동현금흐름 *
label_list = ['현금흐름']
inc_kw_list = []
exc_kw_list = ['손익']

"""

import pandas as pd
import os
import math

class FD_Handler():
    def __init__(self, code):
        self.code = code
        self.saved_dir = 'C:/Git/newFinance_workspace/Financial Data/fsdata/'
        code_list = os.listdir(self.saved_dir)
        for i, file in enumerate(code_list):
            code_list[i] = file.split('.')[0]
        if code not in code_list:
            print('해당 종목 코드의 데이터가 없습니다.')
            return None
        self._load_data()

    def _load_data(self):
        """
        :return:
        self.bs_list    : bs
        self.is_list    : is
        self.cis_list   : cis
        self.ais_list   : is + cis
        self.cf_list    : cf
        self.all_list   : bs + is + cis + cf
        """
        file_name = self.saved_dir + self.code + '.xlsx'
        self.all_list = []

        """
        BS
        [(2020, {dict1}), (2019, {dict2}), ...]
        """
        self.bs_list = []
        try:
            df1 = pd.read_excel(file_name, sheet_name='Data_bs', header=0, engine='openpyxl')
            df2 = pd.read_excel(file_name, sheet_name='Labels_bs', header=0, engine='openpyxl')
            temp = df1.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df1_start_idx = temp.index(temp[-1])
            temp = df2.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df2_start_idx = temp.index(temp[-1])
            _df1 = df1.iloc[:, df1_start_idx:]
            _df2 = df2.iloc[:, df2_start_idx:]
            for i, year in enumerate(list(_df1)):
                label_list = _df2.iloc[:, i].to_list()[2:]
                value_list = _df1.iloc[:, i].to_list()[2:]
                """
                Drop NA values
                """
                drop_idx_list = []
                for j, val in enumerate(value_list):
                    if val == 0 or math.isnan(val):
                        drop_idx_list.append(j)
                label_list = [label for j, label in enumerate(label_list) if j not in drop_idx_list]
                value_list = [value for j, value, in enumerate(value_list) if j not in drop_idx_list]
                year = year[:4]
                temp_dict = dict()
                for j, label in enumerate(label_list):
                    temp_dict[label] = value_list[j]
                self.bs_list.append((year, temp_dict))
                self.all_list.append((year, temp_dict))
        except KeyError:
            pass

        """
        IS (Optional)
        [(2020, {dict1}), (2019, {dict2}), ...]
        """
        self.is_list = []
        try:
            df1 = pd.read_excel(file_name, sheet_name='Data_is', header=0, engine='openpyxl')
            df2 = pd.read_excel(file_name, sheet_name='Labels_is', header=0, engine='openpyxl')
            temp = df1.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df1_start_idx = temp.index(temp[-1])
            temp = df2.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df2_start_idx = temp.index(temp[-1])
            _df1 = df1.iloc[:, df1_start_idx:]
            _df2 = df2.iloc[:, df2_start_idx:]
            for i, year in enumerate(list(_df1)):
                label_list = _df2.iloc[:, i].to_list()[2:]
                value_list = _df1.iloc[:, i].to_list()[2:]
                """
                Drop NA values
                """
                drop_idx_list = []
                for j, val in enumerate(value_list):
                    if val == 0 or math.isnan(val):
                        drop_idx_list.append(j)
                label_list = [label for j, label in enumerate(label_list) if j not in drop_idx_list]
                value_list = [value for j, value, in enumerate(value_list) if j not in drop_idx_list]
                year = year[:4]
                temp_dict = dict()
                for j, label in enumerate(label_list):
                    temp_dict[label] = value_list[j]
                self.is_list.append((year, temp_dict))
            for i, is_tuple in enumerate(self.is_list):
                match_flag = False
                for j, all_tuple in enumerate(self.all_list):
                    if all_tuple[0] == is_tuple[0]:
                        all_tuple[1].update(is_tuple[1])
                        match_flag = True
                        break
                if not match_flag:
                    self.all_list.append(is_tuple)
        except KeyError:
            pass

        """
        CIS
        [(2020, {dict1}), (2019, {dict2}), ...]
        """
        self.cis_list = []
        try:
            df1 = pd.read_excel(file_name, sheet_name='Data_cis', header=0, engine='openpyxl')
            df2 = pd.read_excel(file_name, sheet_name='Labels_cis', header=0, engine='openpyxl')
            temp = df1.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df1_start_idx = temp.index(temp[-1])
            temp = df2.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df2_start_idx = temp.index(temp[-1])
            _df1 = df1.iloc[:, df1_start_idx:]
            _df2 = df2.iloc[:, df2_start_idx:]
            for i, year in enumerate(list(_df1)):
                label_list = _df2.iloc[:, i].to_list()[2:]
                value_list = _df1.iloc[:, i].to_list()[2:]
                """
                Drop NA values
                """
                drop_idx_list = []
                for j, val in enumerate(value_list):
                    if val == 0 or math.isnan(val):
                        drop_idx_list.append(j)
                label_list = [label for j, label in enumerate(label_list) if j not in drop_idx_list]
                value_list = [value for j, value, in enumerate(value_list) if j not in drop_idx_list]
                year = year[:4]
                temp_dict = dict()
                for j, label in enumerate(label_list):
                    temp_dict[label] = value_list[j]
                self.cis_list.append((year, temp_dict))
            for i, cis_tuple in enumerate(self.cis_list):
                match_flag = False
                for j, all_tuple in enumerate(self.all_list):
                    if all_tuple[0] == cis_tuple[0]:
                        all_tuple[1].update(cis_tuple[1])
                        match_flag = True
                        break
                if not match_flag:
                    self.all_list.append(cis_tuple)
        except KeyError:
            pass

        """
        AIS (IS + CIS)
        [(2020, {dict1}), (2019, {dict2}), ...]
        """
        self.ais_list = self.is_list
        for i, cis_tuple in enumerate(self.cis_list):
            match_flag = False
            for j, ais_tuple in enumerate(self.ais_list):
                if ais_tuple[0] == cis_tuple[0]:
                    ais_tuple[1].update(cis_tuple[1])
                    match_flag = True
                    break
            if not match_flag:
                self.ais_list.append(cis_tuple)

        """
        CF
        [(2020, {dict1}), (2019, {dict2}), ...]
        """
        self.cf_list = []
        try:
            df1 = pd.read_excel(file_name, sheet_name='Data_cf', header=0, engine='openpyxl')
            df2 = pd.read_excel(file_name, sheet_name='Labels_cf', header=0, engine='openpyxl')
            temp = df1.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df1_start_idx = temp.index(temp[-1])
            temp = df2.iloc[0].to_list()
            if temp[-1] != "('연결재무제표',)" and temp[-1] != "('별도재무제표',)":
                raise KeyError
            df2_start_idx = temp.index(temp[-1])
            _df1 = df1.iloc[:, df1_start_idx:]
            _df2 = df2.iloc[:, df2_start_idx:]
            for i, year in enumerate(list(_df1)):
                label_list = _df2.iloc[:, i].to_list()[2:]
                value_list = _df1.iloc[:, i].to_list()[2:]
                """
                Drop NA values
                """
                drop_idx_list = []
                for j, val in enumerate(value_list):
                    if val == 0 or math.isnan(val):
                        drop_idx_list.append(j)
                label_list = [label for j, label in enumerate(label_list) if j not in drop_idx_list]
                value_list = [value for j, value, in enumerate(value_list) if j not in drop_idx_list]
                year = year[:4]
                temp_dict = dict()
                for j, label in enumerate(label_list):
                    temp_dict[label] = value_list[j]
                self.cf_list.append((year, temp_dict))
            for i, cf_tuple in enumerate(self.cf_list):
                match_flag = False
                for j, all_tuple in enumerate(self.all_list):
                    if all_tuple[0] == cf_tuple[0]:
                        all_tuple[1].update(cf_tuple[1])
                        match_flag = True
                        break
                if not match_flag:
                    self.all_list.append(cf_tuple)
        except KeyError:
            pass

    def get_data(self, type: str):
        """
        :param type: 'bs', 'is', 'cis', 'ais', 'cf', 'all'
        :return:
        해당 data list
        """
        if type == 'bs':
            return self.bs_list
        elif type == 'is':
            return self.is_list
        elif type == 'cis':
            return self.cis_list
        elif type == 'ais':
            return self.ais_list
        elif type == 'cf':
            return self.cf_list
        elif type == 'all':
            return self.all_list
        else:
            print('올바르지 않은 type입니다.')
            return []

    def get_value(self, year: str, label_list, inc_kw_list, exc_kw_list):
        """
        :param year: 데이터 연도 (e.g. '2020')
        :param label_list: 데이터 라벨 list (e.g. ['유동자산'])
        :param inc_kw_list: label이 포함해야 하는 keyword list
        :param exc_kw_list: label이 포함해선 안되는 keyword list
        :return:
        해당 label, value
        """
        data_list = self.all_list
        for data in data_list:
            if data[0] == year:
                for key, value in data[1].items():
                    for label in label_list:
                        if type(key) == str and label in key:
                            correct_flag = True
                            for inc_kw in inc_kw_list:
                                if inc_kw not in key:
                                    correct_flag = False
                                    break
                            for exc_kw in exc_kw_list:
                                if exc_kw in key:
                                    correct_flag = False
                                    break
                            if correct_flag:
                                return key, value
                break
        return None, None


saved_dir = 'C:/Git/newFinance_workspace/Financial Data/fsdata/'
code_list = os.listdir(saved_dir)
for i, file in enumerate(code_list):
    code_list[i] = file.split('.')[0]
for code in code_list:
    print(code)
    FDH = FD_Handler(code=code)
    label_list = ['현금흐름']
    inc_kw_list = []
    exc_kw_list = ['손익']
    k, v = FDH.get_value(year='2015', label_list=label_list, inc_kw_list=inc_kw_list, exc_kw_list=exc_kw_list)
    print(k, v)

# FDH = FD_Handler(code='000060')
# all_list = FDH.get_data(type='all')
# print(all_list)
# label_list = ['당기순이익', '계속영업이익']
# inc_kw_list = []
# exc_kw_list = ['귀속']
# k, v = FDH.get_value(year='2015', label_list=label_list, inc_kw_list=inc_kw_list, exc_kw_list=exc_kw_list)
# print(k, v)

