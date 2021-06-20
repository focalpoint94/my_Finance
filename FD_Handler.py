
"""
FD_Handler.py
* 사용 예시 *
FDH = FD_Handler(code='110790')
df = FDH.get_dataframe(type='bs')
FDH.get_value('자산총계', '2015')
"""
import pandas as pd


class FD_Handler():
    def __init__(self, code):
        self.code = code
        self._load_data()

    def _load_data(self):
        """
        :return:
        Load bs, cis, cf, all(bs+cis+cf) DataFrame each as
        self.bs_df
        self.cis_df
        self.cf_df
        self.all_df
        """

        saved_dir = 'C:/Git/newFinance_workspace/Financial Data/fsdata/'
        file_name = saved_dir + self.code + '.xlsx'

        df1 = pd.read_excel(file_name, sheet_name=0, header=0, engine='openpyxl')
        df2 = pd.read_excel(file_name, sheet_name=1, header=0, engine='openpyxl')
        temp = df1.iloc[0].to_list()
        start_idx = temp.index('(\'연결재무제표\',)')
        _df1 = df1.iloc[:, start_idx:]
        col_name_list = list(_df1)
        for i, name in enumerate(col_name_list):
            col_name_list[i] = name[:4]
        col_name_list.insert(0, 'Label')
        _df = pd.concat([df2.iloc[:, -1], _df1], axis=1)
        _df.columns = col_name_list
        self.bs_df = _df.drop([_df.index[0], _df.index[1]])

        df1 = pd.read_excel(file_name, sheet_name=2, header=0, engine='openpyxl')
        df2 = pd.read_excel(file_name, sheet_name=3, header=0, engine='openpyxl')
        temp = df1.iloc[0].to_list()
        start_idx = temp.index('(\'연결재무제표\',)')
        _df1 = df1.iloc[:, start_idx:]
        col_name_list = list(_df1)
        for i, name in enumerate(col_name_list):
            col_name_list[i] = name[:4]
        col_name_list.insert(0, 'Label')
        _df = pd.concat([df2.iloc[:, -1], _df1], axis=1)
        _df.columns = col_name_list
        self.cis_df = _df.drop([_df.index[0], _df.index[1]])

        df1 = pd.read_excel(file_name, sheet_name=4, header=0, engine='openpyxl')
        df2 = pd.read_excel(file_name, sheet_name=5, header=0, engine='openpyxl')
        temp = df1.iloc[0].to_list()
        start_idx = temp.index('(\'연결재무제표\',)')
        _df1 = df1.iloc[:, start_idx:]
        col_name_list = list(_df1)
        for i, name in enumerate(col_name_list):
            col_name_list[i] = name[:4]
        col_name_list.insert(0, 'Label')
        _df = pd.concat([df2.iloc[:, -1], _df1], axis=1)
        _df.columns = col_name_list
        self.cf_df = _df.drop([_df.index[0], _df.index[1]])

        self.all_df = pd.concat([self.bs_df, self.cis_df, self.cf_df])

    def get_dataframe(self, type: str):
        """
        :param type: 'bs', 'cis', 'cf'
        :return:
        해당 DataFrame
        """
        if type == 'bs':
            return self.bs_df
        elif type == 'cis':
            return self.cis_df
        elif type == 'cf':
            return self.cf_df
        else:
            print('올바르지 않은 type입니다.')
            return None

    def get_value(self, label, year):
        """
        :param label: 데이터 라벨 (e.g. '유동자산')
        :param year: 데이터 연도 (e.g. '2020')
        :return:
        값
        """
        year_list = list(self.all_df)
        if year not in year_list:
            print('해당 연도 자료가 없습니다.')
            return None
        label_list = self.all_df['Label'].to_list()
        if label not in label_list:
            print('유효하지 않은 Label입니다.')
            return None
        return self.all_df[self.all_df['Label'] == label][year].values[0]

