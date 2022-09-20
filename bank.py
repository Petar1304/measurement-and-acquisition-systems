import serial 
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QLineEdit, QWidget # QVBoxLayout
import sys
from PyQt5.QtCore import QObject, QThread, pyqtSignal

# path variables
PORT = 'dev/tty/ACM0'
IN_FILE_PATH = '/home/petar/Documents/pms/IDbaza.txt'
OUT_FILE_PATH = '/home/petar/Documents/pms/provalnici.txt'

class Worker(QObject):
    # add all signals
    entered_bank = pyqtSignal()
    # signal for changed rfid id
    changed_id = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.num_people = 0
        self.ids = self.load_ids()
        self.known_id = False
    
    def open_serial(self):
        com_port = PORT
        baud_rate = 9600
        ser = serial.Serial(com_port, baud_rate)
        return ser

    # loading codes from file
    def load_ids(self):
        file = IN_FILE_PATH
        with open(file, 'r') as f:
            ids = f.read()
            ids = ids.split('\n')
        return ids

    # write burglars to a text file
    def file_write(self, ID):
        current_time = datetime.now().strftime('%H:%M:%S')
        file = OUT_FILE_PATH
        with open(file, 'a') as f:
            f.write(f'Time {current_time} => ID: {ID}\n')

    # id, distance, touch, volts    
    def process_data(self, data):
        l = data.strip().split(',')
        data_dict = dict()
        data_dict['id'] = l[0]
        data_dict['distance'] = int(l[1])
        data_dict['touch'] = int(l[2])
        data_dict['voltage'] = int(l[3])
        return data_dict

    def process_data_out(self, data):
        formated = ''
        formated += str(data['led_green'])
        formated += str(data['led_red'])
        formated += str(data['display'])
        formated += '\n'
        return formated

    # connected to signal from gui (when someone exits bank)
    def people_sub(self):
        self.num_people -= 1

    # main function
    def run(self):
        # data to send to arduino
        data_out = {
            'led_green': 0,
            'led_red': 0,
            'display': 0
        }
        ser = self.open_serial()
        # sva vrate su zatvorena na pocetku
        first_door = False

        try:
            # add variable for exiting loop and program
            while True:
                arduino_data = ser.readline().decode()
                data_dict = self.process_data(arduino_data)
                
                print(data_dict)

                # calculating max ppl in bank
                max_people_in_bank = data_dict['voltage'] * 4

                # provera da li su prva vrata zatvorena
                if data_dict['distance'] < 10:
                    first_door = False
                else:
                    first_door = True

                # provera dodira
                if data_dict['touch'] == 1 and self.known_id and first_door == False:
                    # ako su prva vrata zatvorena i sensor je dodirnut druga vrata se otvaraju
                    self.num_people += 1
                    self.entered_bank.emit()
                    data_out['led_green'] = 1

                # check id
                if data_dict['id'] != '0':
                    self.changed_id.emit(data_dict['id'])
                    # gasi se zelena lampica
                    data_out['led_green'] = 0
                    data_out['led_red'] = 0

                    if data_dict['id'] in self.ids:
                        print('poznat')
                        self.known_id = True
                        # I vrata se otvaraju
                        if self.num_people < max_people_in_bank:
                            first_door = True
                    # upis nepoznatog id-a u fajl
                    else:
                        self.known_id = False
                        self.file_write(data_dict['id'])
                        data_out['led_red'] = 1

                print(data_out)
                print(self.num_people)
                # write to arduino
                data_out['display'] = self.num_people
                send_data = self.process_data_out(data_out)
                ser.write(send_data.encode())

        except KeyboardInterrupt:
            print('Prekinuto izvrsavanje...')
        except:
            print('Greska...')
        ser.close()

# GUI
class App(QWidget):
    exited_bank = pyqtSignal()

    def __init__(self):
        super().__init__()
        # number of people in bank
        self.num_people = 0
        self.title = 'Bank'
        self.left = 200
        self.top = 200
        self.width = 600
        self.height = 400
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # card id label
        self.card_id = QLabel('CARD ID', self)
        self.card_id.resize(400, 50)
        self.card_id.move(250, 30)

        # code input field
        self.text_input = QLineEdit('Kod', self)
        self.text_input.resize(200, 50)
        self.text_input.move(100, 100)

        # code submit button 
        self.exit_button = QPushButton('IZLAZ', self)
        self.exit_button.resize(100, 50)
        self.exit_button.move(400, 100)
        self.exit_button.clicked.connect(self.exit_bank)

        # notification
        self.notification = QLabel('Obavestenje', self)
        self.notification.resize(400, 100)
        self.notification.move(250, 200)

        # number of people in bank
        self.num_indicator = QLabel(f'Broj ljudi u banci: {self.num_people}', self)
        self.num_indicator.resize(400, 100)
        self.num_indicator.move(250, 240)

        # exit btn
        self.quit_btn = QPushButton('EXIT', self)
        self.quit_btn.resize(100, 50)
        self.quit_btn.move(250, 320)
        self.quit_btn.clicked.connect(QApplication.instance().quit) # closing app
        # self.quit_btn.clicked.connect(self.close_app)
        self.show()

    def close_app(self):
        exit(0)

    # connect changed_id signal
    def change_id(self, new_id):
        self.card_id.setText(new_id)

    def people_add(self):
        self.num_people += 1
        self.num_indicator.setText(f'Broj ljudi u banci: {self.num_people}')

    # CODE = 8888
    def exit_bank(self):
        if self.num_people > -10:
            code = self.text_input.text()
            if code == '8888':
                # emit code signal
                self.num_people -= 1
                self.exited_bank.emit()
                self.num_indicator.setText(f'Broj ljudi u banci: {self.num_people}')
                self.notification.setText('')
            else:
                self.notification.setText('Neispravan Kod')

if __name__ == '__main__':    
    app = QApplication(sys.argv)
    ex = App()

    thread = QThread()

    worker = Worker()
    
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    worker.changed_id.connect(ex.change_id)
    worker.entered_bank.connect(ex.people_add)

    ex.exited_bank.connect(worker.people_sub)
    thread.start()
    
    app.exec_()