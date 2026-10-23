
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtTest
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal

# for yolov5;
# import torch
# from PIL import Image
from PyQt5.QtCore import QBuffer
import io
import os
import numpy as np
import pandas as pd
import glob
import random

import socket #tcpip socket communication;

from datetime import datetime
import time
# import cv2

# to import external file;
import cf # from cf.py
import traceback

try:
    import pyqtgraph as pg
except ImportError:
    pg = None





# form_class = uic.loadUiType("press_main_window.ui")[0]
form_class = uic.loadUiType("megacom.ui")[0]


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
class ThreadOne(QThread):
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    ready = pyqtSignal()


    def __init__(self):
        super().__init__()



    def run(self):
        print("Worker thread started")

        self.ready.emit()





# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
class MainWindow(QMainWindow, form_class):
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    def __init__(self):
        super().__init__()
        self.setupUi(self)


        # ----- to set initial conditions -----
        self.init_variables()


        # ----- thread -----
        self.thread_one = ThreadOne()
        self.thread_one.ready.connect(self.process_threadOne)

        # ----- to connect signals; -----
        self.connect_signals()
        self.init_graph()







    #----------------------------------------------------------------------------------
    def connect_signals(self):
    #----------------------------------------------------------------------------------

#       #to update timer;
        self.BTN_startThread.clicked.connect(self.start_thread)
        self.BTN_fileOpen.clicked.connect(self.file_open)
        self.BTN_run_preprocess.clicked.connect(self.cal_cf_all)  # 실행 버튼: 전체 시간 자동 계산

        # .ui에 없으면 실행 시 예측시간 콤보박스를 자동 생성
        if not hasattr(self, "CmBOX_predictTime"):
            self.CmBOX_predictTime = QComboBox(self)
            self.CmBOX_predictTime.setObjectName("CmBOX_predictTime")
            self.statusBar().addPermanentWidget(self.CmBOX_predictTime)

        self.time_map = {
            "10분": 10, "20분": 20, "30분": 30,
            "1시간": 60, "2시간": 120, "3시간": 180,
            "4시간": 240, "5시간": 300,
        }
        self.CmBOX_predictTime.clear()
        self.CmBOX_predictTime.addItems(self.time_map.keys())

        # Qt Designer에서 BTN_run_all_cf를 만들면 해당 버튼 사용,
        # 없으면 상태표시줄에 '전체 시간 예측' 버튼을 자동 추가
        if not hasattr(self, "BTN_run_all_cf"):
            self.BTN_run_all_cf = QPushButton("전체 시간 예측", self)
            self.BTN_run_all_cf.setObjectName("BTN_run_all_cf")
            self.statusBar().addPermanentWidget(self.BTN_run_all_cf)
        # 별도 버튼은 선택 시간 한 개만 계산하도록 사용
        self.BTN_run_all_cf.setText("선택 시간만 예측")
        self.BTN_run_all_cf.clicked.connect(self.cal_cf)




    #-------------------------------------------------------------------
    def _run_cf_compatible(self, predict_min):
    #-------------------------------------------------------------------
        """신/구 cf.py 모두 지원하고 시간별 파일을 보존한다."""
        import inspect
        import shutil

        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "CF_results"))
        os.makedirs(output_dir, exist_ok=True)
        signature = inspect.signature(cf.calculate_cf)
        kwargs = {"predict_min": int(predict_min)}
        if "output_dir" in signature.parameters:
            kwargs["output_dir"] = output_dir
        if "save_legacy" in signature.parameters:
            kwargs["save_legacy"] = True

        print("CF file:", cf.__file__)
        print("CF signature:", signature)
        raw = cf.calculate_cf(self.df.copy(), **kwargs)
        result = dict(raw) if isinstance(raw, dict) else {}
        result["predict_min"] = int(predict_min)

        # 구버전은 고정된 파일명으로 저장하므로 시간별 이름으로 복사한다.
        legacy_files = {
            "result_file": ("확신도_자동계산_80_85_90도_결과.csv", f"CF_prediction_{predict_min}min.csv"),
            "excel_file": ("확신도_자동생성_80_85_90도_규칙.xlsx", f"CF_rules_{predict_min}min.xlsx"),
            "f1_file": ("F1_Score_결과.csv", f"CF_F1_Score_{predict_min}min.csv"),
        }
        for key, (old_name, new_name) in legacy_files.items():
            current = result.get(key)
            if current and os.path.isfile(current):
                result[key] = os.path.abspath(current)
                continue
            old_path = os.path.abspath(old_name)
            new_path = os.path.join(output_dir, new_name)
            if not os.path.isfile(old_path):
                raise FileNotFoundError(f"CF 결과 파일을 찾을 수 없습니다: {old_path}")
            if os.path.abspath(old_path) != os.path.abspath(new_path):
                shutil.copy2(old_path, new_path)
            result[key] = new_path

        if "result_df" not in result:
            result["result_df"] = pd.read_csv(result["result_file"], encoding="utf-8-sig")
        if "performance_df" not in result:
            result["performance_df"] = pd.read_csv(result["f1_file"], encoding="utf-8-sig")
        return result

    #-------------------------------------------------------------------
    def cal_cf(self):
    #-------------------------------------------------------------------
        """선택한 시간의 CF 결과 저장 및 그래프 표시."""
        if not hasattr(self, "df") or self.df is None or self.df.empty:
            QMessageBox.warning(self, "데이터 없음", "CSV 또는 Excel 파일을 먼저 불러오세요.")
            return
        if self.CmBOX_algorithm.currentText() != "CF-rulebase":
            QMessageBox.warning(self, "알고리즘", "CF-rulebase를 선택하세요.")
            return

        predict_time = self.CmBOX_predictTime.currentText()
        predict_min = self.time_map.get(predict_time, 10)
        try:
            result = self._run_cf_compatible(predict_min)
            self.cf_result = result
            print("예측 결과 저장:", result["result_file"])
            self.plot_cf_results(result)
            QMessageBox.information(self, "예측 완료", f"{predict_time} 예측 완료\n{result['result_file']}")
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "CF 예측 오류", str(exc))

    #-------------------------------------------------------------------
    def cal_cf_all(self):
    #-------------------------------------------------------------------
        """8개 예측 시간별 저장 및 통합 F1 비교표 생성."""
        if not hasattr(self, "df") or self.df is None or self.df.empty:
            QMessageBox.warning(self, "데이터 없음", "CSV 또는 Excel 파일을 먼저 불러오세요.")
            return
        if self.CmBOX_algorithm.currentText() != "CF-rulebase":
            QMessageBox.warning(self, "알고리즘", "CF-rulebase를 선택하세요.")
            return

        self.BTN_run_preprocess.setEnabled(False)
        self.BTN_run_all_cf.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        outputs, failures, frames = {}, [], []
        try:
            for minutes in [10, 20, 30, 60, 120, 180, 240, 300]:
                print(f"\n{'=' * 50}\n{minutes}분 예측 시작\n{'=' * 50}", flush=True)
                self.statusBar().showMessage(f"CF 자동 계산 중: {minutes}분 예측...")
                QApplication.processEvents()
                try:
                    result = self._run_cf_compatible(minutes)
                    outputs[minutes] = result
                    metrics = result["performance_df"].copy()
                    metrics.insert(0, "예측시간(분)", minutes)
                    frames.append(metrics)
                except Exception as exc:
                    traceback.print_exc()
                    failures.append({"예측시간(분)": minutes, "오류": str(exc)})
                QApplication.processEvents()

            save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "CF_results"))
            os.makedirs(save_dir, exist_ok=True)
            summary_file = os.path.join(save_dir, "CF_all_prediction_summary.csv")
            error_file = os.path.join(save_dir, "CF_all_prediction_errors.csv")
            pd.concat(frames, ignore_index=True).to_csv(
                summary_file, index=False, encoding="utf-8-sig"
            ) if frames else pd.DataFrame().to_csv(summary_file, index=False, encoding="utf-8-sig")
            pd.DataFrame(failures, columns=["예측시간(분)", "오류"]).to_csv(
                error_file, index=False, encoding="utf-8-sig"
            )
            self.cf_all_result = {"outputs": outputs, "failures": failures, "summary_file": summary_file}
            if outputs:
                self.plot_cf_results(outputs[max(outputs)])
            message = f"성공: {len(outputs)}개 / 실패: {len(failures)}개\n통합 결과: {summary_file}"
            print(message)
            self.statusBar().showMessage(message, 15000)
            if failures:
                QMessageBox.warning(self, "전체 예측 완료 (일부 실패)", message)
            else:
                QMessageBox.information(self, "전체 예측 완료", message)
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "전체 시간 예측 오류", str(exc))
        finally:
            QApplication.restoreOverrideCursor()
            self.BTN_run_preprocess.setEnabled(True)
            self.BTN_run_all_cf.setEnabled(True)

    #-------------------------------------------------------------------
    def init_graph(self):
    #-------------------------------------------------------------------
        """Qt Designer 그래프용 QWidget이 있으면 pyqtgraph 삽입."""
        self.graph_temp = self.graph_cf = self.graph_f1 = None
        if pg is None:
            print("pyqtgraph 미설치: 그래프 생략 (pip install pyqtgraph)")
            return
        for widget_name, graph_name, title in [
            ("widget_tempGraph", "graph_temp", "Oil Temperature"),
            ("widget_cfGraph", "graph_cf", "Confidence Prediction"),
            ("widget_f1Graph", "graph_f1", "Model Performance"),
        ]:
            container = getattr(self, widget_name, None)
            if container is None:
                continue
            graph = pg.PlotWidget()
            layout = container.layout()
            if layout is None:
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(graph)
            graph.setTitle(title)
            graph.showGrid(x=True, y=True)
            setattr(self, graph_name, graph)

    #-------------------------------------------------------------------
    def plot_cf_results(self, result):
    #-------------------------------------------------------------------
        """현재 실행 결과 파일을 사용하므로 이전 시간 파일과 혼동하지 않음."""
        if pg is None or not isinstance(result, dict):
            return
        df = result.get("result_df")
        if df is None:
            df = pd.read_csv(result["result_file"], encoding="utf-8-sig")
        x = np.arange(len(df))
        if self.graph_temp is not None:
            self.graph_temp.clear()
            self.graph_temp.plot(x, df["current_temp"].to_numpy(),
                                 pen=pg.mkPen("b", width=2))
            self.graph_temp.plot(x, df["actual_future_oil_temp"].to_numpy(),
                                 pen=pg.mkPen("r", width=2))
            self.graph_temp.setTitle(f"Oil Temperature ({result['predict_min']} min)")


        if self.graph_cf is not None:
            self.graph_cf.clear()
            for target, color in [(80, "g"), (85, "y"), (90, "r")]:
                col = f"confidence_{target}"
                if col in df.columns:
                    self.graph_cf.plot(x, df[col].to_numpy(),
                                       pen=pg.mkPen(color, width=2))



        
        if self.graph_f1 is not None:
            scores = result.get("performance_df")
            if scores is None:
                scores = pd.read_csv(result["f1_file"], encoding="utf-8-sig")
            self.graph_f1.clear()
            self.graph_f1.addItem(pg.BarGraphItem(
                x=np.arange(len(scores)), height=scores["F1_Score"].to_numpy(),
                width=0.6, brush="c"))
            self.graph_f1.setYRange(0, 1)


    #----------------------------------------------------------------------------------
    def init_variables(self):
    #----------------------------------------------------------------------------------
        self.pixsizeImg = 600




    #-------------------------------------------------------------------
    def start_thread(self):
    #-------------------------------------------------------------------

        if not self.thread_one.isRunning():
            # Start thread
            self.thread_one.start()


    #-------------------------------------------------------------------
    def process_threadOne(self):
    #-------------------------------------------------------------------

        print('hello, threadone')



    #-------------------------------------------------------------------
    def file_open(self):
    #-------------------------------------------------------------------

        print('hello, file open;')

        self.loading_filename, _ = QFileDialog.getOpenFileName(
            self, 
            'Open datafile', 
            './', 
            filter="Data Files (*.csv *.xlsx *.xls)")
        # Extract the filename only (without the path)

        if not self.loading_filename:
            print('No file selected')
            return

        # Extract filename only
        self.loaded_filename = os.path.basename(self.loading_filename)
        print(f'Loading file; {self.loaded_filename}') 

        # Show filename on Qlabel
        self.LBL_loadedFilename.setText(self.loaded_filename)


        # --------------------------------------------------
        # Load dataframe
        # --------------------------------------------------

        try:

            print('Loading file...')

            # Load dataframe 
            if self.loaded_filename.lower().endswith('.csv'):

                print('Reading CSV...')

                try:
                    self.df = pd.read_csv(
                        self.loading_filename,
                        encoding='utf-8-sig'
                    )
                    print('CSV encoding: UTF-8')

                except UnicodeDecodeError:
                    print('UTF-8 failed. Trying CP949...')

                    self.df = pd.read_csv(
                        self.loading_filename,
                        encoding='cp949'
                    )
                    print('CSV encoding: CP949')


            elif self.loaded_filename.lower().endswith(('.xlsx', '.xls')):

                print('Full path: ', self.loading_filename)    


                print('Reading Excel...')

                self.df = pd.read_excel(self.loading_filename)

                # Create CSV filename
                csv_filename = os.path.splitext(
                    self.loading_filename
                )[0] + '.csv'

                print('Converting to CSV...')
                self.df.to_csv(
                    csv_filename,
                    index=False,
                    encoding='utf-8-sig'
                )

                print(f'CSV saved: {csv_filename}')

            else:
                print('Unsupported file type')
                return
            
            print('df.shape; ', self.df.shape)
            print(self.df.tail())
            
        except Exception as e:
            print('Error loading dataframe: ', e)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # simple run process
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@






# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
if __name__ == "__main__":
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    app = QApplication(sys.argv)
    my_Window = MainWindow()
    my_Window.show()



    sys.exit(app.exec_())


