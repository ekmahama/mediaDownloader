import sys
import os
from PySide2 import QtGui
from PySide2.QtCore import QThread, Signal
import youtube_dl
from PySide2.QtWidgets import (QWidget, QPushButton, QFileDialog,
                               QLabel, QLineEdit, QMainWindow, QGridLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QTableView, QHBoxLayout,
                               QVBoxLayout, QApplication)


class MyLogger():
    """This class is required for youtube_dl per documentation """

    def debug(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)


class DownloadThread(QThread):
    """A thread that will execute the download """
    data_downloaded = Signal()

    def __init__(self, directory, url, row_position):
        super().__init__()
        self.ydl_opt = {'logger': MyLogger(),
                        'outtmpl': os.path.join(directory, '%(title)s.%(ext)s'),
                        'progress_hook': [self.my_hook]}

        self.url = url
        self.row_position = row_position

    def my_hook(self, data):
        filename = data.get('filename').split('/')[-1].split('.')[0]
        data = (filename, data.get('_percent_str', '100%'), self.row_position)
        self.data_downloaded.emit(data)

    def run(self):
        with youtube_dl.YoutubeDL(self.ydl_opt) as ydl:
            ydl.download([self.url])


class MainWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.threads = []
        self.initUI()
        self.setup_connections()

    def initUI(self):
        """
        This method creates the widget of interest
        """
        # Widget for logo (if any)
        self.logo_label = QLabel(self)
        logo = QtGui.QPixmap("logo.jpg")
        self.logo_label.setPixmap(logo)

        # use horizontal layout for the logo
        logoBox = QHBoxLayout()
        logoBox.addStretch(1)
        logoBox.addWidget(self.logo_label)
        logoBox.addStretch(1)

        # Widget for for url label
        self.url_label = QLabel(self)

        # Widget for for url input
        self.url_label.setText('Url:')
        self.url_input = QLineEdit(self)

        # Widget for locatin label
        self.location_label = QLabel(self)
        self.location_label.setText('Location:')
        self.location_input = QLineEdit(self)

        # Widget for browse & download button
        self.browse_btn = QPushButton("Browse")
        self.download_btn = QPushButton("Download")

        # Place widgets on a grid
        # input to addWidet(widget, row, col, row-span, col-span, alignment)
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.url_label, 0, 0)
        grid.addWidget(self.url_input, 0, 1, 1, 2)

        grid.addWidget(self.location_label, 1, 0)
        grid.addWidget(self.location_input, 1, 1)

        grid.addWidget(self.browse_btn, 1, 2)
        grid.addWidget(self.download_btn, 2, 0, 1, 3)

        # Table widget
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.verticalHeader().setVisible(False)  # hide row labels

        self.tableWidget.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)  # fit the remaining space after col 2 take its space
        self.tableWidget.setColumnWidth(1, 140)
        self.tableWidget.setShowGrid(False)  # done show gridline
        # select entire row when one cell is selected
        self.tableWidget.setSelectionBehavior(QTableView.SelectRows)
        self.tableWidget.setHorizontalHeaderLabels(["Filename", "Downloaded"])

        # use vertical layout for logo, grid and make as default layout
        vbox = QVBoxLayout()
        vbox.addLayout(logoBox)
        vbox.addLayout(grid)
        vbox.addWidget(self.tableWidget)
        self.setLayout(vbox)

    def setup_connections(self):
        self.browse_btn.clicked.connect(self.pick_location)
        self.download_btn.clicked.connect(self.start_download)

    def pick_location(self):
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(self, "Select Folder")
        self.location_input.setText(folder_path)

    def start_download(self):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
        self.tableWidget.setItem(
            row_position, 0, QTableWidgetItem(self.url_input.text()))
        self.tableWidget.setItem(row_position, 1, QTableWidgetItem("100%"))

        downloader = DownloadThread(
            self.location_input.text(), self.url_input.text(), row_position)

        downloader.data_downloaded.connect(self.on_data_ready)
        self.threads.append(downloader)
        downloader.start()

    def on_data_ready(self, data):
        self.tableWidget.setItem(data[2], 0, QTableWidgetItem(data[0]))
        self.tableWidget.setItem(data[2], 1, QTableWidgetItem(data[1]))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        m_widget = MainWidget(self)
        self.setCentralWidget(m_widget)
        self.setGeometry(300, 300, 700, 350)
        self.setWindowTitle('Dowloader v0.1')


if __name__ == '__main__':
    app = QApplication(sys.argv)  # this run our app
    m_window = MainWindow()
    m_window.show()
    # Starts the main applicatio loop (some widget do neet it though)
    sys.exit(app.exec_())
