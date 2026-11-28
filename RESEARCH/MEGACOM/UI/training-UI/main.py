import sys, codecs
from pathlib import Path
from datetime import datetime
from PyQt5 import QtWidgets as W, QtCore as C, uic
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
ROOT = Path(__file__).resolve().parent
H = (10,30,60,120)
T = (80,85,90)

class TrainingWindow(W.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(ROOT/'training.ui'), self)
        self.process = None
        self.loss, self.pred, self.results = {}, {}, {}
        self.dateStart.setDate(C.QDate.currentDate().addMonths(-3))
        self.dateEnd.setDate(C.QDate.currentDate())
        self.cmbHumidity.setCurrentIndex(1)
        self.txtLog.setMaximumBlockCount(20000)
        self.tableResult.horizontalHeader().setSectionResizeMode(W.QHeaderView.Stretch)
        self.tableResult.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.axes = []
        for layout in (self.lossLayout,self.predictionLayout):
            fig = Figure(facecolor='#142137', tight_layout=True)
            canvas = FigureCanvasQTAgg(fig)
            layout.addWidget(canvas)
            self.axes.append((fig.add_subplot(111),canvas))
        self.timer = C.QTimer(self)
        self.timer.timeout.connect(self.draw)
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnCSV.clicked.connect(self.csv)
        self.btnClear.clicked.connect(self.txtLog.clear)
        self.cmbModel.currentIndexChanged.connect(self.setup)
        self.cmbHumidity.currentIndexChanged.connect(self.humidity)
        self.btnSaveLog.clicked.connect(self.save_log)
        self.btnLoadData.clicked.connect(self.check_data)
        self.cmbViewHorizon.currentIndexChanged.connect(self.refresh_view)
        self.setup(); self.humidity(); self.draw(); self.status('READY')
    def log(self,s):
        self.txtLog.appendPlainText(f'[{datetime.now():%H:%M:%S}] {s}')
    def status(self,s):
        self.trainingStatus.setText('● '+s); self.statusbar.showMessage(s)
    def humidity(self,*_):
        self.chk_io048.setEnabled(self.cmbHumidity.currentIndex()!=2)
        if self.cmbHumidity.currentIndex()==2: self.chk_io048.setChecked(False)
    def setup(self,*_):
        cf=self.cmbModel.currentText()=='CF'
        for w in (self.spinEpoch,self.spinBatch,self.spinSequence): w.setEnabled(not cf)
        for t in T: getattr(self,f'chk{t}').setEnabled(cf)
        self.loss.clear(); self.pred.clear(); self.results.clear()
        self.refresh_view()
    def selected_horizon(self):
        return H[self.cmbViewHorizon.currentIndex()]
    def refresh_view(self, *_):
        h=self.selected_horizon()
        cf=self.cmbModel.currentText()=='CF'
        self.rows={(h,t):i for i,t in enumerate(T if cf else (None,))}
        self.tableResult.clearContents(); self.tableResult.setRowCount(len(self.rows))
        for (h,t),i in self.rows.items():
            self.cell(i,0,f'{h} min'); self.cell(i,1,t if t else '-')
            for c,v in enumerate(self.results.get((h,t),()),5 if cf else 2): self.cell(i,c,v)
        self.tableResult.setMinimumHeight(150 if cf else 95)
        self.draw()
    def cell(self,r,c,v):
        item=W.QTableWidgetItem(str(v)); item.setTextAlignment(C.Qt.AlignCenter); self.tableResult.setItem(r,c,item)
    def csv(self):
        p,_=W.QFileDialog.getOpenFileName(self,'CSV',str(ROOT),'CSV (*.csv)')
        if p:
            self.txtCSV.setText(p)
            self.check_data()
    def check_data(self):
        p=Path(self.txtCSV.text().strip())
        if p.is_file() and p.suffix.lower()=='.csv':
            self.log(f'CSV: {p.name} / {p.stat().st_size:,} bytes')
        else:
            self.log('CSV 파일을 선택하세요.')
    def save_log(self):
        p,_=W.QFileDialog.getSaveFileName(self,'Save log',str(ROOT/'training.log'),'Log (*.log)')
        if p:
            try: Path(p).write_text(self.txtLog.toPlainText(),encoding='utf-8')
            except OSError as e: self.log(str(e))
    def start(self):
        if self.process: return
        model=self.cmbModel.currentText().lower(); source='csv'
        features=[w.objectName()[4:] for w in self.groupFeatures.findChildren(W.QCheckBox) if w.isChecked()]
        horizons=[str(h) for h in H if getattr(self,f'chk{h}').isChecked()]
        thresholds=[str(t) for t in T if getattr(self,f'chk{t}').isChecked()]
        mode=('actual','mean','exclude')[self.cmbHumidity.currentIndex()]
        if mode=='exclude': features=[f for f in features if f!='io048']
        if not features or not horizons or not self.companyEdit.text().strip() or (model=='cf' and not thresholds) or self.dateStart.date()>self.dateEnd.date():
            self.log('Invalid training settings'); return
        script=ROOT/f'train_{model}.py'
        if not script.is_file(): self.log(f'Missing training script: {script}'); return
        args=['-u',str(script),'--comcode',self.companyEdit.text().strip(),'--device-id',self.cmbDevice.currentText(),'--source',source,'--start-date',self.dateStart.date().toString('yyyy-MM-dd'),'--end-date',self.dateEnd.date().toString('yyyy-MM-dd'),'--features',','.join(features),'--horizons',','.join(horizons),'--humidity-mode',mode,'--learning-rate',str(self.spinLR.value())]
        if model=='cf': args+=['--thresholds',','.join(thresholds)]
        else: args+=['--epochs',str(self.spinEpoch.value()),'--batch-size',str(self.spinBatch.value()),'--sequence-length',str(self.spinSequence.value())]
        csv_path=Path(self.txtCSV.text().strip())
        if not csv_path.is_file() or csv_path.suffix.lower()!='.csv':
            self.log('학습용 CSV 파일을 먼저 선택하세요.'); return
        args+=['--csv-path',str(csv_path.resolve())]
        self.setup(); self.cmbViewHorizon.setCurrentIndex(H.index(int(horizons[0]))); self.progressBar.setValue(0)
        self.buffer=''; self.decoder=codecs.getincrementaldecoder('utf-8')(errors='replace'); self.stopped=False
        p=self.process=C.QProcess(self); p.setWorkingDirectory(str(ROOT)); p.setProcessChannelMode(C.QProcess.MergedChannels)
        env=C.QProcessEnvironment.systemEnvironment(); env.insert('PYTHONIOENCODING','utf-8'); p.setProcessEnvironment(env)
        p.readyReadStandardOutput.connect(self.read); p.finished.connect(self.finished); p.errorOccurred.connect(self.error)
        self.running(True); self.status('TRAINING'); self.timer.start(500); p.start(sys.executable,args)
    def running(self,b):
        self.btnStart.setEnabled(not b); self.btnStop.setEnabled(b)
        self.groupData.setEnabled(not b); self.groupFeatures.setEnabled(not b)
        for w in [self.cmbModel,self.cmbHumidity,self.spinLR,self.spinEpoch,self.spinBatch,self.spinSequence]+[getattr(self,f'chk{x}') for x in H+T]: w.setEnabled(not b)
        if not b:
            cf=self.cmbModel.currentText()=='CF'
            for w in (self.spinEpoch,self.spinBatch,self.spinSequence): w.setEnabled(not cf)
            for t in T: getattr(self,f'chk{t}').setEnabled(cf)
            self.humidity()
    def read(self):
        if not self.process: return
        self.buffer+=self.decoder.decode(bytes(self.process.readAllStandardOutput()))
        while '\n' in self.buffer:
            line,self.buffer=self.buffer.split('\n',1); self.parse(line.strip())
    def parse(self,line):
        if not line: return
        self.log(line); a=line.split()
        try:
            if a[0]=='PROGRESS': self.progressBar.setValue(max(0,min(100,int(a[1]))))
            elif a[0]=='LOSS': self.loss.setdefault(int(a[1]),[]).append(tuple(map(float,a[2:5])))
            elif a[0]=='PRED':
                d=self.pred.setdefault(int(a[1]),[]); d.append(tuple(map(float,a[2:4]))); del d[:-1000]
            elif a[0] in ('CF_RESULT','LSTM_RESULT'):
                cf=a[0]=='CF_RESULT'; key=(int(a[1]),int(a[2]) if cf else None)
                vals=a[3:6] if cf else a[2:5]
                self.results[key]=[f'{float(v):.4f}' if v.upper()!='N/A' else v for v in vals]
                if key in self.rows: self.refresh_view()
        except (ValueError,IndexError): self.log('Invalid output format')
    def draw(self):
        for i,(ax,canvas) in enumerate(self.axes):
            ax.clear(); ax.set_facecolor('#0D192B'); ax.tick_params(colors='#DCE7F5'); ax.grid(alpha=.2)
            h=self.selected_horizon()
            for rows in [(self.loss if i==0 else self.pred).get(h,[])]:
                if not rows: continue
                cols=list(zip(*rows))
                if i==0: ax.plot(cols[0],cols[1],label=f'{h}m Train'); ax.plot(cols[0],cols[2],'--',label=f'{h}m Validation')
                else: ax.plot(cols[0],label=f'{h}m Actual'); ax.plot(cols[1],'--',label=f'{h}m Predicted')
            ax.set_xlabel('Epoch' if i==0 else 'Sample',color='#DCE7F5'); ax.set_ylabel('Loss' if i==0 else 'Temperature (°C)',color='#DCE7F5')
            ax.set_title(f"{h} min", color="#DCE7F5", fontsize=10)
            if ax.lines: ax.legend(fontsize=8, loc="upper right", facecolor="#20334D", labelcolor="#DCE7F5")
            else: ax.text(.5,.5,"No data",transform=ax.transAxes,ha="center",va="center",color="#DCE7F5")
            canvas.draw_idle()
    def stop(self):
        if self.process:
            self.stopped=True; p=self.process; self.status('STOPPING'); p.terminate(); C.QTimer.singleShot(3000,lambda: p.kill() if self.process is p else None)
    def error(self,e):
        if self.process: self.log(self.process.errorString())
        if e==C.QProcess.FailedToStart: self.status('FAILED'); self.reset()
    def finished(self,code,status):
        if not self.process: return
        self.read(); self.buffer+=self.decoder.decode(b'',final=True); self.parse(self.buffer.strip())
        ok=code==0 and status==C.QProcess.NormalExit and not self.stopped
        if ok: self.progressBar.setValue(100)
        self.status('COMPLETED' if ok else 'STOPPED' if self.stopped else 'FAILED'); self.draw(); self.reset()
    def reset(self):
        self.timer.stop(); p=self.process; self.process=None
        if p: p.deleteLater()
        self.running(False)
    def closeEvent(self,event):
        if self.process:
            if W.QMessageBox.question(self,'Exit','Stop training and exit?')!=W.QMessageBox.Yes: event.ignore(); return
            self.stopped=True; self.process.kill(); self.process.waitForFinished(3000)
        event.accept()

if __name__=='__main__':
    app=W.QApplication(sys.argv); app.setStyle('Fusion'); window=TrainingWindow(); window.showMaximized(); sys.exit(app.exec_())
