import os, sys, shutil
from pathlib import Path
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, uic

ROOT=Path(__file__).resolve().parent

# ROOT = Path(
#     r"C:\CHERLHEE\AI_waytogo\RESEARCH\MEGACOM"
#     r"\UI\MEGACOM_PyQt_Designer_GUI\megacom_gui"
# )




FILES={'rule':'rule.py','cf':'cf.py','lstm':'lstm_predict.py'}

class Dashboard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(ROOT/'dashboard.ui'),self)
        self.folder=ROOT
        self.processes={}
        self.setStyleSheet(STYLE)


        from PyQt5.QtGui import QFont
        # 실행 로그 글꼴 설정
        # font = QFont("함초롬돋움", 10)
        # self.logEdit.setFont(font)
        font = QFont("Pretendard", 10)
        self.logEdit.setFont(font)


        self.dataTable.setColumnCount(7)
        self.dataTable.setHorizontalHeaderLabels(['측정 시각','오일온도 °C','부하율 %','전력 kW','압력','유량','습도'])
        self.dataTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.dataTable.verticalHeader().hide()
        self.dataTable.setAlternatingRowColors(True)
        for key in FILES:
            getattr(self,key+'Start').clicked.connect(lambda _,k=key:self.start(k))
            getattr(self,key+'Stop').clicked.connect(lambda _,k=key:self.stop(k))
            getattr(self,key+'Stop').setEnabled(False)
        self.folderButton.clicked.connect(self.choose_folder)
        self.refreshButton.clicked.connect(self.refresh)
        self.clearButton.clicked.connect(self.logEdit.clear)
        self.log('준비 완료. 스크립트 및 의존 파일을 같은 프로젝트 폴더에 배치하세요.')
        self.log('CF 모델 JSON, LSTM config.py / lstm_features.py / 모델 파일은 기존 경로가 필요합니다.')
        self.timer=QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(15000)
    def log(self,message):
        self.logEdit.appendPlainText(f'[{datetime.now():%H:%M:%S}] {message}')
        bar=self.logEdit.verticalScrollBar();bar.setValue(bar.maximum())
    def choose_folder(self):
        d=QtWidgets.QFileDialog.getExistingDirectory(self,'분석 스크립트 폴더',str(self.folder))
        if d:self.folder=Path(d);self.log('스크립트 경로: '+d)
    def start(self,key):
        if key in self.processes and self.processes[key].state()!=QtCore.QProcess.NotRunning:return
        script=self.folder/FILES[key]
        if not script.exists():
            self.log(f'{key.upper()} 실행 실패: {script} 파일 없음')
            return
        proc=QtCore.QProcess(self)
        proc.setWorkingDirectory(str(self.folder))
        proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)



        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUNBUFFERED', '1')
        env.insert('PYTHONIOENCODING', 'utf-8')
        env.insert('PYTHONUTF8', '1')
        proc.setProcessEnvironment(env)
        
        
        
        proc.readyReadStandardOutput.connect(lambda k=key,p=proc:self.read_output(k,p))
        proc.errorOccurred.connect(lambda err,k=key,p=proc:self.log(f'{k.upper()} 프로세스 오류: {p.errorString()}'))
        proc.finished.connect(lambda code,status,k=key:self.finished(k,code))
        args=[str(script),'--interval',str(self.intervalSpin.value())]




        # CF 모델 경로 지정
        if key == 'cf':

            model_dir = self.folder / "cf_11_output"

            model_file = model_dir / "cf_11_model.json"
            temp_model_file = model_dir / "cf_11_temperature_model.json"

            if not model_file.is_file():
                self.log(f"CF 모델 파일 없음: {model_file}")
                return

            if not temp_model_file.is_file():
                self.log(f"CF 온도 모델 파일 없음: {temp_model_file}")
                return

            args.extend([
                "--model", str(model_file),
                "--temperature-model", str(temp_model_file)
            ])



        if key=='lstm':args+=['--comcode',self.companyEdit.text().strip(),'--device-id',self.deviceEdit.text().strip()]
        # rule.py와 cf.py의 장비 설정은 각각 소스 상수/환경 설정에서 읽음.
        proc.start(sys.executable,args)
        if not proc.waitForStarted(3000):
            self.log(f'{key.upper()} 시작 실패: {proc.errorString()}');return
        self.processes[key]=proc
        getattr(self,key+'Status').setText('● 실행 중')
        getattr(self,key+'Start').setEnabled(False)
        getattr(self,key+'Stop').setEnabled(True)
        self.connectionLabel.setText('●  분석 실행 중')
        self.log(f'{key.upper()} 시작: {sys.executable} {" ".join(args)}')

    def read_output(self,key,proc):
        data=bytes(proc.readAllStandardOutput())
        for line in data.decode('utf-8',errors='replace').splitlines():
            if line.strip():self.log(f'[{key.upper()}] {line[:900]}')
    def stop(self,key):
        proc=self.processes.get(key)
        if proc and proc.state()!=QtCore.QProcess.NotRunning:
            proc.terminate()
            QtCore.QTimer.singleShot(2500,lambda p=proc:p.kill() if p.state()!=QtCore.QProcess.NotRunning else None)
            self.log(f'{key.upper()} 중지 요청')
    def finished(self,key,code):
        getattr(self,key+'Status').setText('● 중지')
        getattr(self,key+'Start').setEnabled(True)
        getattr(self,key+'Stop').setEnabled(False)
        self.log(f'{key.upper()} 종료 (코드 {code})')
        if not any(p.state()!=QtCore.QProcess.NotRunning for p in self.processes.values()):
            self.connectionLabel.setText('●  엔진 대기')
    def refresh(self):
        # GUI는 DB를 읽기만 합니다. 분석/저장은 원본 스크립트가 수행합니다.
        try:
            import mysql.connector
            from dotenv import load_dotenv
            load_dotenv(self.folder/'mysql_config.env')
            cfg=dict(host=os.getenv('MYSQL_HOST') or os.getenv('DB_HOST'),
                     port=int(os.getenv('MYSQL_PORT') or os.getenv('DB_PORT') or 3307),
                     user=os.getenv('MYSQL_USER') or os.getenv('DB_USER'),
                     password=os.getenv('MYSQL_PASSWORD') or os.getenv('DB_PASSWORD'),
                     database=os.getenv('MYSQL_DATABASE') or os.getenv('DB_NAME') or 'airpredict',
                     connection_timeout=4)
            if not cfg['host'] or not cfg['user']:
                self.log('DB 조회 건너뜀: mysql_config.env의 MYSQL_HOST / MYSQL_USER 설정 필요')
                return
            conn=mysql.connector.connect(**cfg)
            try:
                cur=conn.cursor()
                cur.execute('SELECT input_time,io003,io028,io010,io044,io046,io048 FROM ai_data WHERE comcode=%s AND deviceId=%s ORDER BY input_time DESC LIMIT 20',(self.companyEdit.text().strip(),self.deviceEdit.text().strip()))
                rows=cur.fetchall();cur.close()
            finally:conn.close()
            self.dataTable.setRowCount(len(rows))
            for i,row in enumerate(rows):
                for j,val in enumerate(row):
                    item=QtWidgets.QTableWidgetItem('—' if val is None else str(val))
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                    self.dataTable.setItem(i,j,item)
            self.dataHint.setText(f'최근 {len(rows)}건 조회 · {datetime.now():%H:%M:%S}')
        except Exception as exc:self.log('DB 조회 실패: '+str(exc))
    def closeEvent(self,event):
        active=[k for k,p in self.processes.items() if p.state()!=QtCore.QProcess.NotRunning]
        if active:
            reply=QtWidgets.QMessageBox.question(self,'종료 확인','실행 중인 분석 엔진을 중지하고 종료하시겠습니까?')
            if reply!=QtWidgets.QMessageBox.Yes:event.ignore();return
            for k in active:
                p=self.processes[k];p.terminate()
                if not p.waitForFinished(1200):p.kill();p.waitForFinished(1200)
        event.accept()

STYLE='''
QMainWindow,QWidget#centralwidget{background:#0B1220;color:#DCE6F5;font-family:"Malgun Gothic","Segoe UI";font-size:12px}
QLabel#title{font-size:25px;font-weight:800;color:#F8FAFC}
QLabel#subtitle,QLabel#footer,QLabel#dataHint{color:#8494AC;font-size:12px}
QLabel#connectionLabel{color:#42D6A4;font-size:14px;font-weight:700}
QFrame#line{background:#25344A;border:none}
QLabel#deviceTitle,QLabel#cardsTitle,QLabel#dataTitle,QLabel#logsTitle{font-size:17px;font-weight:700;color:#F1F5FB}
QFrame#ruleCard,QFrame#cfCard,QFrame#lstmCard{background:#142137;border:1px solid #263A56;border-radius:15px}
QLabel#ruleName,QLabel#cfName,QLabel#lstmName{font-size:17px;font-weight:800;color:#F5F8FF;background:transparent}
QLabel#ruleDesc,QLabel#cfDesc,QLabel#lstmDesc{color:#9AAEC9;background:transparent}
QLabel#ruleStatus,QLabel#cfStatus,QLabel#lstmStatus{color:#45D9AB;background:transparent;font-weight:700}
QLineEdit,QDoubleSpinBox{background:#17263D;border:1px solid #314563;border-radius:7px;padding:6px;color:white}
QPushButton{background:#223754;color:#EAF2FF;border:1px solid #345075;border-radius:8px;font-weight:700;padding:5px}
QPushButton:hover{background:#31547D}
QPushButton:disabled{color:#63738B;background:#172438;border-color:#23344B}
QPushButton#ruleStart,QPushButton#cfStart,QPushButton#lstmStart{background:#176A72;border-color:#228A8E}
QPushButton#ruleStart:hover,QPushButton#cfStart:hover,QPushButton#lstmStart:hover{background:#208C91}
QTableWidget,QPlainTextEdit{background:#101D30;color:#D9E7F6;border:1px solid #2A405F;border-radius:9px;gridline-color:#263B56;selection-background-color:#255C87;alternate-background-color:#16263D}
QHeaderView::section{background:#213652;color:#E6F0FF;padding:8px;border:none;border-right:1px solid #344A67;font-weight:700}
'''
if __name__=='__main__':
    app=QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    win=Dashboard();win.show()
    sys.exit(app.exec_())
