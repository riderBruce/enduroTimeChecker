from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtGui

import sys
from datetime import datetime, timedelta
import pandas as pd

Enduro_Time_Checker = uic.loadUiType("ui/maintable.ui")[0]

DIFFERENTIAL_SECOND = 60
ADVANTAGE_WOMAN = -30
ADVANTAGE_SENIOR = -20
PENALTY_10 = 10
PENALTY_30 = 30


class ViewEnduroTimeChecker(QMainWindow, Enduro_Time_Checker):
    def __init__(self):
        super().__init__()
        column_name = ['id', 'name', 'woman', 'senior', '+10s', '+30s']
        self.df_man = pd.DataFrame(columns=column_name)
        column_name = ['id', 'name', 'time', 'check', 'del']
        self.df_time = pd.DataFrame(columns=column_name)
        column_name = ['id', 'name', 'start', 'finish', 'record', 'rank', 'adjust', 'sum', 'gap', 'final']
        self.df_result = pd.DataFrame(columns=column_name)

        self.time_checker_counter = 0

        self.initUI()
        self.showMaximized()

    def initUI(self):
        self.setupUi(self)

        self.show_table_man(self.df_man, self.table_man)
        self.show_on_table_by_time(self.df_time, self.table_time)
        self.show_table_result(self.df_result, self.table_result)

        self.input_id.setReadOnly(True)
        self.input_name.setReadOnly(True)
        self.input_id_time.setReadOnly(True)

        self.btn_register.clicked.connect(self.register_name)
        self.btn_save_man.clicked.connect(lambda: self.save_csv_file(self.df_man, "man"))
        self.btn_load_man.clicked.connect(self.load_man_file)
        # self.btn_clear_man.clicked.connect(self.clear_man_table)

        self.btn_start.clicked.connect(self.time_checker)
        self.btn_save_time.clicked.connect(lambda: self.save_csv_file(self.df_time, "time"))
        self.btn_load_time.clicked.connect(self.load_time_file)
        # self.btn_clear_time.clicked.connect(self.clear_time_table)

        self.btn_get_result.clicked.connect(self.get_result)
        self.btn_save_result.clicked.connect(lambda: self.save_csv_file(self.df_result, "result"))

    # 영역 나누기
    def register_name(self):
        self.btn_register.setStyleSheet('QPushButton {background-color: #AA0044; color: #ffffff; font:bold; border-width: 4px;}')
        self.btn_start.setStyleSheet('QPushButton {background-color: #ffffff; color: #000000; border: none;}')
        self.input_id.setReadOnly(False)
        self.input_name.setReadOnly(False)
        self.input_id_time.setReadOnly(True)
        self.input_id.setFocus()
        self.input_id.returnPressed.connect(self.input_name.setFocus)
        self.input_name.returnPressed.connect(self.input_man_to_table)

    def time_checker(self):
        self.btn_start.setStyleSheet('QPushButton {background-color: #AA0044; color: #ffffff; font:bold; border-width: 4px;}')
        self.btn_register.setStyleSheet('QPushButton {background-color: #ffffff; color: #000000; border: none;}')
        self.input_id_time.setReadOnly(False)
        self.input_id.setReadOnly(True)
        self.input_name.setReadOnly(True)
        self.input_id_time.setFocus()
        self.input_id_time.returnPressed.connect(self.input_time_to_table)
        self.save_csv_file(self.df_man, "man")

    def get_result(self):
        self.result_calculator()
        self.show_table_result(self.df_result, self.table_result)
        # self.save_csv_file(self.df_result, "result")

    def result_calculator(self):
        # ['id', 'name', 'woman', 'senior', '+10s', '+30s']
        # ['id', 'name', 'time', 'check', 'del']
        # ['id', 'name', 'start', 'finish', 'record', 'rank', 'adjust', 'sum', 'gap', 'final']
        df = self.df_time.copy()
        df_man = self.df_man.copy()

        df = df[['id']]
        df = df.drop_duplicates(subset='id', keep='last')

        df = pd.merge(df, df_man[['id', 'name']], how='left', on='id')
        df['name'] = df['name'].apply(lambda x: x if not pd.isnull(x) else 'unclear')
        df = df[['id', 'name']]

        if df_man.empty:
            QMessageBox.about(self, 'confirm', 'there is no data of man')
            return
        df_man['adjust_sec'] = (df_man['woman'] * ADVANTAGE_WOMAN
                            + df_man['senior'] * ADVANTAGE_SENIOR
                            + df_man['+10s'] * PENALTY_10
                            + df_man['+30s'] * PENALTY_30)

        df_time = self.df_time
        df_time = df_time.drop_duplicates(subset=['id', 'check'], keep='last')

        df_start = df_time[df_time['check'] == 'start']
        df_start = df_start.rename(columns={'time': 'start'})
        df = pd.merge(df, df_start[['id', 'start']], how='left', on='id')

        df_finish = df_time[df_time['check'] == 'finish']
        df_finish = df_finish.rename(columns={'time': 'finish'})
        df = pd.merge(df, df_finish[['id', 'finish']], how='left', on='id')

        df['record'] = df['finish'] - df['start']
        df['rank'] = df['record'].rank(method='min')

        df = pd.merge(df, df_man[['id', 'adjust_sec']], how='left', on='id')
        df['adjust'] = df['adjust_sec'].apply(lambda x: timedelta(seconds=x) if not pd.isnull(x) else timedelta(seconds=0))
        df['sum'] = df['record'] + df['adjust']
        df['final'] = df['sum'].rank(method='min')

        df = df.sort_values(by='final')

        df[['gap']] = df[['sum']].diff()
        df['adjust'] = df['adjust_sec']
        df['record'] = df['record'].apply(lambda x: str(x)[-12:-4] if not pd.isnull(x) else "")
        df['sum'] = df['sum'].apply(lambda x: str(x)[-12:-4] if not pd.isnull(x) else "")
        df['gap'] = df['gap'].apply(lambda x: str(x)[-12:-4] if not pd.isnull(x) else "")

        df = df[['id', 'name', 'start', 'finish', 'record', 'rank', 'adjust', 'sum', 'gap', 'final']]
        self.df_result = df

    # 인풋 컨트롤 -----------------

    def input_man_to_table(self):
        id = self.input_id.text()
        if id == '':
            self.clear_input_id_name()
        name = self.input_name.text()
        self.df_man.loc[len(self.df_man)] = [id, name, False, False, False, False]
        self.df_man.drop_duplicates(subset=['id'], keep='last', inplace=True)
        self.df_man = self.df_man.loc[self.df_man['id'] != '']
        self.df_man.reset_index(drop=True, inplace=True)
        self.show_table_man(self.df_man, self.table_man)
        self.clear_input_id_name()

    def input_time_to_table(self):
        # autosave when 10 times input
        self.time_checker_counter += 1
        if self.time_checker_counter % 10 == 0:
            self.save_csv_file(self.df_time, "time")

        id = self.input_id_time.text()
        if id == '':
            self.clear_input_id_time()
            return
        self.df_man = self.df_man.astype({'id': 'string'})
        if len(self.df_man) == 0:
            name = 'unclear'
        elif len(self.df_man.loc[self.df_man['id'] == id]) == 0:
            name = 'unclear'
        else:
            name = self.df_man.loc[self.df_man['id'] == id, 'name'].tolist()[0]

        time = datetime.now()

        check = self.insert_start_finish_on_time_table(id, time)

        self.df_time = pd.merge(self.df_time[['id', 'time', 'check', 'del']],
                                self.df_man[['id', 'name']], on='id', how='left')
        self.df_time['name'] = self.df_time['name'].apply(lambda x: x if not pd.isnull(x) else 'unclear')
        self.df_time = self.df_time[['id', 'name', 'time', 'check', 'del']]

        self.df_time.loc[len(self.df_time)] = [id, name, time, check, '']
        self.show_on_table_by_time(self.df_time, self.table_time)
        self.clear_input_id_time()

    def insert_start_finish_on_time_table(self, id, time) -> str:
        # 첫번째 기록 -> 시작을 기록
        # 두번째 이상부터는
        # 60초이상 차이가 나지 않은 경우
        # 기존 start를 na화하고
        # start를 기록,
        # 마지막 기록이 finish인 이후에 찍히는 것은 na처리

        df = self.df_time.copy()

        # 최초의 계측
        if len(df) == 0:
            check = "start"
            return check

        # 해당 아이디의 최초의 계측
        if len(df.loc[df['id'] == id]) == 0:                # 처음 태깅인 경우 시작을 기록
            check = "start"
            return check

        # 이미 finish데이터가 있는 경우
        if len(df.loc[(df['id'] == id) & (df['check'] == 'finish')]):
            check = "na"
            return check

        # 정해진 시간 내에 다시 태깅하는 경우, start를 na로 하고 최근 계측을 start로 처리
        rule = timedelta(seconds=DIFFERENTIAL_SECOND)
        previous_time = df.loc[(df['id'] == id) & (df['check'] == 'start')]['time'].iloc[-1]
        gap_between_tagging = time - previous_time

        if gap_between_tagging <= rule:                                 # 두번째 태그한 시간이 정해진 시간보다 작으면
            df.loc[df['time'] == previous_time, 'check'] = "na"     # 기존 계측을 na로 하고
            check = "start"                                         # 신규 check를 시작으로 한다.
            self.df_time = df
            return check

        # 정상적인 종료의 경우
        check = "finish"                           # 정해진 시간보다 크면 이번 기록을 종료로 한다.
        self.df_time = df
        return check

    def re_calculation_all_check(self):
        df = self.df_time.copy()
        df_temp = pd.DataFrame()
        rule = timedelta(seconds=DIFFERENTIAL_SECOND)
        for d, k in df.groupby(['id']):
            # d는 유니크값, k는 각 데이터 프레임
            # get the difference this time with previous time
            k[['gap']] = k[['time']].diff()
            # get the difference previous time with this time
            k[['gap2']] = k[['time']].diff(periods=-1)
            k['gap2'] = - k['gap2']

            is_not_there_start = not ("start" in [x for x in k['check']])
            is_not_there_finish = not ("finish" in [x for x in k['check']])
            is_last_start = (k['check'].iloc[-1] == 'start')
            max_time = k['time'].max()

            k['check'] = k.apply(lambda x: "finish" if (x['gap'] > rule) else \
                                            "start" if (x['gap2'] > rule) else \
                                            "start" if (len(k) == 1) else \
                                            "start" if (is_not_there_start & is_not_there_finish & (x['time'] == max_time)) else \
                                            "start" if (is_last_start & (x['time'] == max_time)) else \
                                            "na", axis=1)
            df_temp = pd.concat([df_temp, k], ignore_index=True)

        df_temp = df_temp[['id', 'time', 'check', 'del']]
        df_temp = pd.merge(df_temp, self.df_man[['id', 'name']], how='left', on='id')
        df_temp = df_temp[['id', 'name', 'time', 'check', 'del']]
        df_temp = df_temp.sort_values(by='time')
        df_temp = df_temp.reset_index(drop=True)
        self.df_time = df_temp

    def click_event_delete_each_time(self):
        button = self.sender()
        button_loc = self.table_time.indexAt(button.pos())
        row_num = button_loc.row()

        is_void = (self.df_time.iloc[row_num].check == 'na')
        self.df_time = self.df_time.drop(row_num)
        self.df_time = self.df_time.reset_index(drop=True)
        if not is_void:
            self.re_calculation_all_check()
        self.show_on_table_by_time(self.df_time, self.table_time)

    def click_event_check_penalty(self):
        check_box = self.sender()
        check_box_loc = self.table_man.indexAt(check_box.parent().pos())
        row = check_box_loc.row()
        col = check_box_loc.column()
        self.df_man.iloc[row, col] = check_box.isChecked()


    def clear_input_id_name(self):
        self.input_id.clear()
        self.input_name.clear()
        self.input_id.setFocus()

    def clear_input_id_time(self):
        self.input_id_time.clear()
        self.input_id_time.setFocus()

    # 불러오기 -------------------------------------
    def load_man_file(self):
        file_name = self.get_file_name()
        if not file_name:
            return
        man_temp = pd.read_csv(file_name, encoding='utf-8-sig')
        if man_temp.columns.to_list() != ['id', 'name', 'woman', 'senior', '+10s', '+30s']:
            QMessageBox.about(self, 'confirm', 'this is an invalid format file')
            return
        man_temp = man_temp.astype({'id': 'string'})
        self.df_man = man_temp
        self.show_table_man(self.df_man, self.table_man)

    def load_time_file(self):
        file_name = self.get_file_name()
        if not file_name:
            return
        time_temp = pd.read_csv(file_name, encoding='utf-8-sig')
        if time_temp.columns.to_list() != ['id', 'name', 'time', 'check', 'del']:
            QMessageBox.about(self, 'confirm', 'this is an invalid file.')
            return
        time_temp = time_temp.astype({'id': 'string'})
        self.df_time = time_temp
        self.df_time['time'] = pd.to_datetime(self.df_time['time'])
        self.show_on_table_by_time(self.df_time, self.table_time)

    def get_file_name(self):
        fname = QFileDialog.getOpenFileName(self, 'Open File')
        file_name = fname[0]  # 파일이름은 0번째
        if file_name == '':
            QMessageBox.about(self, 'confirm', "It's canceled.")
            return None
        return file_name

    # 초기화 ----------------------------
    def clear_man_table(self):
        self.df_man = self.df_man.iloc[:0]
        self.show_table_man(self.df_man, self.table_man)
        self.clear_input_id_name()
        self.register_name()

    def clear_time_table(self):
        self.df_time = self.df_time.iloc[:0]
        self.show_on_table_by_time(self.df_time, self.table_time)
        self.clear_input_id_time()
        self.time_checker()

    # 파일 저장 --------------------------
    def save_csv_file(self, df, category):
        df = df.astype({'id': 'string'})
        # output_file = QFileDialog.getSaveFileName(self, 'CSV 저장', '', 'CSV (*.csv)')
        # output_file_name = output_file[0]
        output_file_name = category + "_" + datetime.now().strftime('%Y%m%d_%H%M') + '.csv'
        if output_file_name == '':
            QMessageBox.about(self, 'confirm', "It's canceled.")
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            df.to_csv(output_file_name, index=False, encoding='utf-8-sig')
            QApplication.restoreOverrideCursor()
            # QMessageBox.about(self, '확인', "저장이 완료되었습니다.")


    # table setting ----------------------------------------
    def show_table_man(self, df, table):
        # QtableWidget 테이블 자동 세팅
        self.set_qtable_column_nums(df, table)

        # # # # 수동 헤더
        header = table.horizontalHeader()
        header.resizeSection(0, 60)
        header.resizeSection(1, 60)
        header.resizeSection(2, 50)
        header.resizeSection(3, 50)
        header.resizeSection(4, 50)
        header.resizeSection(5, 50)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        # 데이터 채워넣기
        self.set_data_into_qtable(df[['id', 'name']], table)

        # add toggle button on last 3 column
        for i in range(len(df.index)):
            for j in range(2, len(df.columns)):
                is_checked = bool(df.iat[i, j])
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                check_box = QCheckBox()
                check_box.setChecked(is_checked)
                layout.addWidget(check_box)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0,0,0,0)
                cell_widget.setLayout(layout)
                table.setCellWidget(i, j, cell_widget)
                check_box.stateChanged.connect(self.click_event_check_penalty)

        # 데이터 좌우 정렬
        alignSetting = 'l,c'  # 6개 중에서 2개만 자동 정렬
        self.align_qtable(alignSetting, df, table)

        # # qtable columns color
        # for i in df.index:
        #     table.item(i, 2).setBackground(QtGui.QColor(234, 244, 250))
        #     table.item(i, 4).setBackground(QtGui.QColor(234, 244, 250))
        #     table.item(i, 6).setBackground(QtGui.QColor(234, 244, 250))

        table.setStyleSheet(
            "QTableView::item:selected { color:white; background:#AA0044; font-weight:900; }"
            "QTableCornerButton::section { background-color:#232326; }"
            "QHeaderView::section { color:white; background-color:#232326; }")


    def show_on_table_by_time(self, df, table):
        # add delete button
        df['del'] = ""
        # QtableWidget 테이블 자동 세팅
        self.set_qtable_column_nums(df, table)

        # # # # 수동 헤더
        header = table.horizontalHeader()
        header.resizeSection(0, 160)
        header.resizeSection(1, 120)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.resizeSection(3, 50)
        header.resizeSection(4, 30)

        # 데이터 채워넣기
        self.set_data_into_qtable(df, table)

        # add delete button on last column
        for i in range(len(df.index)):
            j = len(df.columns) - 1
            pb = QPushButton('del')
            pb.clicked.connect(self.click_event_delete_each_time)
            table.setCellWidget(i, j, pb)

        # 데이터 좌우 정렬
        alignSetting = 'l,c,c,c,c'  # 4개
        self.align_qtable(alignSetting, df, table)

        # # qtable columns color
        # for i in df.index:
        #     table.item(i, 2).setBackground(QtGui.QColor(234, 244, 250))
        #     table.item(i, 4).setBackground(QtGui.QColor(234, 244, 250))
        #     table.item(i, 6).setBackground(QtGui.QColor(234, 244, 250))

        table.setStyleSheet(
            "QTableView::item:selected { color:white; background:#AA0044; font-weight:900; }"
            "QTableCornerButton::section { background-color:#232326; }"
            "QHeaderView::section { color:white; background-color:#232326; }")

        if len(df):
            self.get_result()

    def show_table_result(self, df, table):
        # column_name = ['id', 'name', 'start', 'finish', 'record', 'rank', 'adjust', 'sum', 'gap', 'final']

        # QtableWidget 테이블 자동 세팅
        self.set_qtable_column_nums(df, table)

        # # # # 수동 헤더
        header = table.horizontalHeader()
        header.resizeSection(0, 100)
        header.resizeSection(1, 100)
        header.resizeSection(2, 200)
        header.resizeSection(3, 200)
        header.resizeSection(4, 120)
        header.resizeSection(5, 120)
        header.resizeSection(6, 120)
        header.resizeSection(7, 150)
        header.resizeSection(8, 150)
        header.resizeSection(9, 100)
        header.setSectionResizeMode(9, QHeaderView.Stretch)

        # 데이터 채워넣기
        self.set_data_into_qtable(df, table)

        # 데이터 좌우 정렬
        alignSetting = 'l,c,c,c,c,c,c,c,c,c'  # 10개
        self.align_qtable(alignSetting, df, table)

        # # qtable columns color
        for i in df.index:
            table.item(i, 5).setBackground(QtGui.QColor(234, 244, 250))
            table.item(i, 9).setBackground(QtGui.QColor(234, 244, 250))

        table.setStyleSheet(
            "QTableView::item:selected { color:white; background:#AA0044; font-weight:900; }"
            "QTableCornerButton::section { background-color:#232326; }"
            "QHeaderView::section { color:white; background-color:#232326; }")

    def set_qtable_column_nums(self, df, table):
        # QtableWidget 테이블 자동 세팅
        table.clear()
        table.setColumnCount(len(df.columns))
        table.setRowCount(len(df.index))
        column_name_list = list(df.columns.values.tolist())
        column_name_list = [str(i) for i in column_name_list]
        table.setHorizontalHeaderLabels(column_name_list)

    def set_data_into_qtable(self, df, table):
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))  # 데이터 넣기
                table.item(i, j).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # 가운데 정렬

    def align_qtable(self, alignSetting, df, table):
        # 데이터 좌우 정렬
        # alignSetting = 'c,c,c,c,r,r,c,r,c,c,c'  # 11개
        alignSetting_lst = alignSetting.split(',')
        for i in range(len(df.index)):  # 행
            for j in enumerate(alignSetting_lst):  # 열
                if j[1] == 'c':
                    table.item(i, j[0]).setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # 가운데 정렬
                elif j[1] == 'l':
                    table.item(i, j[0]).setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                elif j[1] == 'r':
                    table.item(i, j[0]).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                else:
                    print("정렬 오류")


if __name__ == "__main__":
    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    # WindowClass의 인스턴스 생성
    myWindow = ViewEnduroTimeChecker()
    # 프로그램 화면을 보여주는 코드
    myWindow.show()
    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
