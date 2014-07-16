from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWebKitWidgets import QWebView
import sys


class MainWindow(QMainWindow):
    def __init__(self, url):
        super(MainWindow, self).__init__()
        self.view = QWebView(self)
        self.view.load(url)
        self.view.setFixedSize(890, 550)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)


class FileWindow(QFileDialog):
    def __init__(self):
        super(QFileDialog, self).__init__()
        self.dir_path = ''

    def get_dir_path(self):
        self.dir_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        return self.dir_path


def display_webkit_window():
    app = QApplication(sys.argv)
    url_to_display = QUrl('http://127.0.0.1:5000/')
    browser = MainWindow(url_to_display)
    browser.show()
    browser.setFixedSize(890, 550)
    sys.exit(app.exec_())


def display_dir_dialog():
    app = QApplication(sys.argv)
    get_dir = FileWindow()
    dir_path = get_dir.get_dir_path()
    return dir_path
    #print('path:' + dir_path)