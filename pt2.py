from PyQt5.QtCore import QObject, QThread, pyqtSignal
import PyQt5.QtWidgets as qtw
import sys
import time

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    run_thread = True
    i = 1
        
    def run(self):
        while(self.run_thread): # Simulacija akvizicije
            time.sleep(1)
            self.progress.emit(self.i)
            self.i += 1
        self.finished.emit()


class App(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.clicksCount = 0
        self.rt = True
        self.setupUI()
    
    def setupUI(self):
        self.setWindowTitle("Zadatak")
        self.resize(300, 150)
        self.centralWidget = qtw.QWidget()
        self.setCentralWidget(self.centralWidget)
        
        self.clicksLabel = qtw.QLabel("Brojac: 0 klikova", self)
        self.stepLabel = qtw.QLabel("Korak dugog zadatka: 0")
        
        self.countBtn = qtw.QPushButton("Klikni", self)
        self.countBtn.clicked.connect(self.countClicks)
        
        self.longRunningBtn = qtw.QPushButton("Dug zadatak", self)
        self.longRunningBtn.clicked.connect(self.runLongTask)
        
        self.stopBtn = qtw.QPushButton("Kraj", self)
        self.stopBtn.clicked.connect(self.stopFcn)
        
        layout = qtw.QVBoxLayout()
        layout.addWidget(self.clicksLabel)
        layout.addWidget(self.countBtn)
        layout.addWidget(self.stepLabel)
        layout.addWidget(self.longRunningBtn)
        layout.addWidget(self.stopBtn)
        self.centralWidget.setLayout(layout)
        
    def countClicks(self):
        self.clicksCount += 1
        self.clicksLabel.setText("Brojac: " + str(self.clicksCount) +  " klikova")

    def reportProgress(self, n):
        self.worker.run_thread = self.rt # Zaustavljanje akvizicje
        self.stepLabel.setText("Korak dugog zadatka: " + str(n))
        
    def stopFcn(self):
        self.rt = False

    def runLongTask(self):
        # Napraviti nit
        self.thread = QThread()
        # Napraviti objekat klase Worker
        self.worker = Worker()
        # Spajanje "radnika" sa niti
        self.worker.moveToThread(self.thread)
        
        # Povezati sve signale
        # Prvo se aktivira funkcija "run"
        self.worker.run_thread = True
        self.thread.started.connect(self.worker.run)
        # Spaja se signal koji oznacava da je funkcija u thread-u gotova 
        # kako bi se thread obrisao
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # Spaja se signal koji prenosi informacije tokom ozvrsavanja same 
        # funkcije unutar "radnika"
        self.worker.progress.connect(self.reportProgress)
        
        # Startovanje niti
        self.thread.start()
        
        # Kad se nit zavrsi vrednost koraka se opet postavlja na 0
        self.thread.finished.connect(
            lambda: self.stepLabel.setText("Korak dugog zadatka: 0")
        )
    
        
app = qtw.QApplication(sys.argv)
win = App()
win.show()
app.exec_()