# -*- coding: utf-8 -*-

import main

import os
import sys
import threading
import shutil

from flask import Flask, g, render_template
import flask_sijax
from gevent.wsgi import WSGIServer

from PyQt5.QtCore import Qt, QUrl, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWebKitWidgets import QWebView


######################### General variables #########################
local_path = os.path.realpath('.')


######################### Flask code #########################
# initialise app
flask_app = Flask(__name__)

# config for flask-sijax
flask_app.config["CACHE_TYPE"] = "null"
flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
flask_app.config["SIJAX_STATIC_PATH"] = os.path.join(main.local_path, 'static', 'js', 'sijax')
flask_sijax.Sijax(flask_app)


class SijaxHandler(object):
    @staticmethod
    def set_progress(obj_response):
        try:
            progress_file = open(os.path.join(local_path, 'files', '.progress_file.txt'), 'r+b')
            progress_file_text = progress_file.read()
            progress_file.close()

            print(progress_file_text)
            progress_bar_value = progress_file_text[1:] + '%'

            if progress_file_text[0] == 'c':
                obj_response.html('#progress_state', 'Stage 1 of 5: compressing...')
                obj_response.css('#pgb1', 'width', progress_bar_value)
                obj_response.html('#pgb1-label', progress_bar_value)
            elif progress_file_text[0] == 'i':
                obj_response.css('#pgb1', 'width', '100%')
                obj_response.html('#pgb1-label', '100%')

                obj_response.html('#progress_state', 'Stage 2 of 5: generating unique ID...')
                obj_response.css('#pgb2', 'width', progress_bar_value)
                obj_response.html('#pgb2-label', progress_bar_value)
            elif progress_file_text[0] == 's':
                obj_response.css('#pgb2', 'width', '100%')
                obj_response.html('#pgb2-label', '100%')

                obj_response.html('#progress_state', 'Stage 3 of 5: splitting archive...')
                obj_response.css('#pgb3', 'width', progress_bar_value)
                obj_response.html('#pgb3-label', progress_bar_value)
            elif progress_file_text[0] == 'e':
                obj_response.css('#pgb3', 'width', '100%')
                obj_response.html('#pgb3-label', '100%')

                obj_response.html('#progress_state', 'Stage 4 of 5: encrypting files...')
                obj_response.css('#pgb4', 'width', progress_bar_value)
                obj_response.html('#pgb4-label', progress_bar_value)
            elif progress_file_text[0] == 'u':
                obj_response.css('#pgb4', 'width', '100%')
                obj_response.html('#pgb4-label', '100%')

                obj_response.html('#progress_state', 'Stage 5 of 5: uploading files...')
                obj_response.css('#pgb5', 'width', progress_bar_value)
                obj_response.html('#pgb5-label', progress_bar_value)
            elif progress_file_text[0] == 'f':
                obj_response.css('#pgb5', 'width', '100%')
                obj_response.html('#pgb5-label', '100%')

                upload_archive_id = progress_file_text[1:]
                obj_response.attr('#upload_id', 'value', upload_archive_id)

                obj_response.script(
                    "$('#upload_button').removeClass('btn-default').addClass('btn-success');"
                    "$('#upload_spinner').removeClass('fa-spinner fa-spin').addClass('fa-check');"
                    "$('#upload_txt').html(' Upload Complete');")
                obj_response.script("$.fn.fullpage.moveSectionUp();")  # move up one slide

                progress_file = open(os.path.join(local_path, 'files', '.progress_file.txt'), 'w+b')
                progress_file.write('0')
                progress_file.close()

            elif progress_file_text[0] == 'g':
                obj_response.html('#d_progress_state', 'Stage 1 of 5: downloading files...')
                obj_response.css('#d_pgb1', 'width', progress_bar_value)
                obj_response.html('#d_pgb1-label', progress_bar_value)
            elif progress_file_text[0] == 'd':
                obj_response.css('#d_pgb1', 'width', '100%')
                obj_response.html('#d_pgb1-label', '100%')

                obj_response.html('#d_progress_state', 'Stage 2 of 5: decrypting...')
                obj_response.css('#d_pgb2', 'width', progress_bar_value)
                obj_response.html('#d_pgb2-label', progress_bar_value)
            elif progress_file_text[0] == 'm':
                obj_response.css('#d_pgb2', 'width', '100%')
                obj_response.html('#d_pgb2-label', '100%')

                obj_response.html('#d_progress_state', 'Stage 3 of 5: concatenating files...')
                obj_response.css('#d_pgb3', 'width', progress_bar_value)
                obj_response.html('#d_pgb3-label', progress_bar_value)
            elif progress_file_text[0] == 'v':
                obj_response.css('#d_pgb3', 'width', '100%')
                obj_response.html('#d_pgb3-label', '100%')

                obj_response.html('#d_progress_state', 'Stage 4 of 5: checking download integrity...')
                obj_response.css('#d_pgb4', 'width', progress_bar_value)
                obj_response.html('#d_pgb4-label', progress_bar_value)
            elif progress_file_text[0] == 'x':
                obj_response.css('#d_pgb4', 'width', '100%')
                obj_response.html('#d_pgb4-label', '100%')

                obj_response.html('#d_progress_state', 'Stage 5 of 5: extracting archive...')
                obj_response.css('#d_pgb5', 'width', progress_bar_value)
                obj_response.html('#d_pgb5-label', progress_bar_value)
            elif progress_file_text[0] == 'j':
                obj_response.css('#d_pgb5', 'width', '100%')
                obj_response.html('#d_pgb5-label', '100%')

                save_path = progress_file_text[1:]
                obj_response.attr('#download_location', 'value', save_path)

                obj_response.script(
                    "$('#download_button').removeClass('btn-default').addClass('btn-success');"
                    "$('#download_spinner').removeClass('fa-spinner fa-spin').addClass('fa-check');"
                    "$('#download_txt').html(' Download Complete');")
                obj_response.script("$.fn.fullpage.moveSectionDown();")  # move down one slide

                progress_file = open(os.path.join(local_path, 'files', '.progress_file.txt'), 'w+b')
                progress_file.write('0')
                progress_file.close()

            elif progress_file_text[0] == '0':
                print('no progress')
                obj_response.html('#progress_state', '')
                obj_response.html('#d_progress_state', '')
                progress_bar_value = ''
                obj_response.css('.progress-bar', 'width', progress_bar_value)
                obj_response.html('.progress-bar-label', progress_bar_value)

                obj_response.script(
                    "$('#upload_button').removeClass('btn-success').addClass('btn-default');"
                    "$('#upload_spinner').removeClass('fa-check').addClass('fa-cloud-upload');"
                    "$('#upload_txt').html(' Upload');"
                    "$('#dir_to_upload_path').val('');"
                    "$('#passphrase_field').val('');"
                    "$('#upload_button').prop('disabled', false);"
                    "$('#download_button').removeClass('btn-success').addClass('btn-default');"
                    "$('#download_spinner').removeClass('fa-check').addClass('fa-cloud-download');"
                    "$('#download_txt').html(' Download');"
                    "$('#archive_id').val('');"
                    "$('#save_path').val('');"
                    "$('#decrypt_passphrase_field').val('');"
                    "$('#download_button').prop('disabled', false);")

                progress_file = open(os.path.join(local_path, 'files', '.progress_file.txt'), 'w+b')
                progress_file.write('')
                progress_file.close()
        except Exception as e:
            print(e)
            pass

    @staticmethod
    def start_upload(obj_response, dir_to_upload_path, passphrase):
        t = threading.Thread(target=main.upload_private, args=(dir_to_upload_path, passphrase,))
        t.start()

    @staticmethod
    def start_download(obj_response, archive_id, save_path, passphrase):
        tr = threading.Thread(target=main.download_private, args=(archive_id, save_path, passphrase,))
        tr.start()

    @staticmethod
    def choose_dir_to_upload(obj_response):
        try:
            dir_path = MainWindow.display_dir_dialog()
        except:
            dir_path = ''
        obj_response.attr('#dir_to_upload_path', 'value', dir_path)

    @staticmethod
    def load_server_public_key(obj_response):
        try:
            file_path = MainWindow.display_file_dialog()
        except:
            file_path = ''

        if not file_path == '':
            shutil.copy(file_path[0], os.path.join(local_path, 'keys'))

        obj_response.script(
            "$('#server_public_key_btn').removeClass('btn-default').addClass('btn-success');"
            "$('#server_public_key_btn').prepend('<span class=\"fa fa-check\"></span> ');"
        )

    @staticmethod
    def choose_public_key_save_path(obj_response):
        try:
            dir_path = MainWindow.display_dir_dialog()
        except:
            dir_path = ''
        obj_response.attr('#public_key_save_path', 'value', dir_path)


@flask_sijax.route(flask_app, '/')
def index():
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()

    return render_template('view_1.html')


def start_server():
    http_server = WSGIServer(('', 62494), flask_app)
    http_server.serve_forever()


######################### PyQt GUI code #########################
class FlaskThread(QThread):
    def run(self):
        start_server()


class MainWindow(QMainWindow):
    def __init__(self, url):
        super(MainWindow, self).__init__()
        self.view = QWebView(self)
        self.view.load(url)
        self.view.setFixedSize(890, 550)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)

    @staticmethod
    def display_dir_dialog():
        dialog = QFileDialog()
        dir_path = QFileDialog.getExistingDirectory(dialog, "Select Directory")
        return dir_path

    @staticmethod
    def display_file_dialog():
        dialog = QFileDialog()
        file_path = QFileDialog.getOpenFileName(dialog, "Select File")
        return file_path


def display_webkit_window():
    qt_app = QApplication(sys.argv)
    thread = FlaskThread()
    thread.start()
    url_to_display = QUrl('http://127.0.0.1:62494/')
    browser = MainWindow(url_to_display)
    browser.show()
    browser.setFixedSize(890, 550)
    sys.exit(qt_app.exec_())


if __name__ == '__main__':
    display_webkit_window()