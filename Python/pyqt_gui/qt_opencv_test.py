import cv2
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from qtpy import QtWidgets


class Capture:
    def __init__(self):
        self.capturing = False
        self.c = cv2.VideoCapture(0)

    def startCapture(self):
        print "pressed start"
        self.capturing = True
        cap = self.c
        while (self.capturing):
            ret, frame = cap.read()
            cv2.imshow("Capture", frame)
            cv2.waitKey(5)
        cv2.destroyAllWindows()

    def endCapture(self):
        print "pressed End"
        self.capturing = False

    def quitCapture(self):
        print "pressed Quit"
        cap = self.c
        cv2.destroyAllWindows()
        cap.release()
        QtCore.QCoreApplication.quit()


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('Control Panel')

        self.capture = Capture()
        self.start_button = QtWidgets.QPushButton('Start', self)
        self.start_button.clicked.connect(self.capture.startCapture)

        self.end_button = QtWidgets.QPushButton('End', self)
        self.end_button.clicked.connect(self.capture.endCapture)

        self.quit_button = QtWidgets.QPushButton('Quit', self)
        self.quit_button.clicked.connect(self.capture.quitCapture)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.end_button)
        vbox.addWidget(self.quit_button)

        self.setLayout(vbox)
        self.setGeometry(100, 100, 200, 200)
        self.show()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())
