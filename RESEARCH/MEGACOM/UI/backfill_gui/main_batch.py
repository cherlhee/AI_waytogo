import sys
from pathlib import Path
from PyQt5 import QtWidgets as W, QtCore as C
from batch_common import DEVICES
ROOT=Path(__file__).resolve().parent
class Dashboard(W.QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('MEGACOM Historical Backfill');self.resize(850,600);self.jobs={}
        layout=W.QVBoxLayout(self);form=W.QFormLayout();layout.addLayout(form)
        self.company=W.QLineEdit('C00088');form.addRow('Company',self.company)
        self.start_date=W.QDateEdit(C.QDate(2026,11,1));self.end_date=W.QDateEdit(C.QDate(2026,11,1))
        for label,w in [('Start date',self.start_date),('End date (inclusive)',self.end_date)]:w.setCalendarPopup(True);w.setDisplayFormat('yyyy-MM-dd');form.addRow(label,w)
        self.device=W.QComboBox();self.device.addItems(['ALL',*DEVICES]);form.addRow('Device',self.device)
        self.batch=W.QSpinBox();self.batch.setRange(1,10000);self.batch.setValue(100);form.addRow('Batch size',self.batch)
        self.ig=W.QSpinBox();self.ig.setRange(0,10000);self.ig.setValue(12);form.addRow('LSTM IG every N predictions (0=off)',self.ig)
        self.log=W.QPlainTextEdit();self.log.setReadOnly(True)
        self.buttons={}
        for key in ('rule','cf','lstm'):
            row=W.QHBoxLayout();start=W.QPushButton('Start '+key.upper());stop=W.QPushButton('Stop '+key.upper());stop.setEnabled(False);row.addWidget(start);row.addWidget(stop);layout.addLayout(row);self.buttons[key]=(start,stop)
            start.clicked.connect(lambda _,k=key:self.run(k));stop.clicked.connect(lambda _,k=key:self.stop(k))
        allbtn=W.QPushButton('Start all');allbtn.clicked.connect(lambda:[self.run(k) for k in self.buttons]);layout.addWidget(allbtn);layout.addWidget(W.QLabel('Historical RULE: ai_analysis only; no ai_alarm writes.'));layout.addWidget(self.log)
    def run(self,k):
        if k in self.jobs:return
        if self.start_date.date()>self.end_date.date() or not self.company.text().strip():W.QMessageBox.warning(self,'Invalid settings','Check dates and company');return
        args=[str(ROOT/f'{k}_batch.py'),'--start-date',self.start_date.date().toString('yyyy-MM-dd'),'--end-date',self.end_date.date().toString('yyyy-MM-dd'),'--comcode',self.company.text().strip(),'--batch-size',str(self.batch.value())]
        if self.device.currentText()!='ALL':args+=['--device-id',self.device.currentText()]
        if k=='lstm':args+=['--explain-every',str(self.ig.value())]
        p=C.QProcess(self);p.setWorkingDirectory(str(ROOT));p.setProcessChannelMode(C.QProcess.MergedChannels);env=C.QProcessEnvironment.systemEnvironment();env.insert('PYTHONUNBUFFERED','1');env.insert('PYTHONIOENCODING','utf-8');p.setProcessEnvironment(env)
        p.readyReadStandardOutput.connect(lambda:self.read(k,p));p.finished.connect(lambda code,status:self.finish(k,p,code));p.errorOccurred.connect(lambda err:self.log.appendPlainText(f'[{k}] {p.errorString()}'))
        self.jobs[k]=p;self.buttons[k][0].setEnabled(False);self.buttons[k][1].setEnabled(True);p.start(sys.executable,args)
        if not p.waitForStarted(3000):self.finish(k,p,-1)
    def read(self,k,p):
        s=bytes(p.readAllStandardOutput()).decode('utf-8',errors='replace');self.log.appendPlainText(f'[{k.upper()}] {s.rstrip()}')
    def finish(self,k,p,code):
        if self.jobs.get(k) is not p:return
        self.read(k,p);self.jobs.pop(k);self.buttons[k][0].setEnabled(True);self.buttons[k][1].setEnabled(False);self.log.appendPlainText(f'[{k}] exit={code}');p.deleteLater()
    def stop(self,k):
        p=self.jobs.get(k)
        if p:p.terminate();C.QTimer.singleShot(2000,lambda:self.kill_if_active(k,p))
    def kill_if_active(self,k,p):
        if self.jobs.get(k) is p and p.state()!=C.QProcess.NotRunning:p.kill()
    def closeEvent(self,e):
        for p in list(self.jobs.values()):p.kill();p.waitForFinished(2000)
        e.accept()
if __name__=='__main__':
    app=W.QApplication(sys.argv);w=Dashboard();w.show();sys.exit(app.exec_())
