from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebKitWidgets import QWebView
import sys

class MainWindow(QMainWindow):
	def __init__(self, url):
		super(MainWindow, self).__init__()

		self.view = QWebView(self)
		self.view.load(url)
		self.view.setFixedSize(900,550)
		self.view.setContextMenuPolicy(Qt.NoContextMenu)

if __name__ == '__main__':
	app = QApplication(sys.argv)

	url = QUrl('http://127.0.0.1:5000/')

	browser = MainWindow(url)
	browser.show()
	browser.setFixedSize(900,550)

	sys.exit(app.exec_())