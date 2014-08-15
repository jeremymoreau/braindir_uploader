# -*- coding: utf-8 -*-

import main

import os
import sys
import threading
import json
import socket

from flask import Flask, g, render_template
import flask_sijax
from gevent.wsgi import WSGIServer

from PyQt5.QtCore import Qt, QUrl, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWebKitWidgets import QWebView

# not used, but cx_freeze build fails if not included
from PyQt5 import QtNetwork, QtWebKit, QtPrintSupport
import jinja2.ext

######################### Set up data directories #########################
# get appdata directory root
appdata_path = main.appdata_path

# set local path root depending on whether app is packaged or not
if hasattr(sys, 'frozen'):
    local_path = os.path.dirname(os.path.realpath(sys.executable))
else:
    local_path = os.path.dirname(os.path.realpath(sys.argv[0]))

# set templates and static folders path
templates_path = os.path.join(local_path, 'templates')
static_path = os.path.join(local_path, 'static')

######################### Get an unused port #########################
flask_socket = socket.socket()
flask_socket.bind(('', 0))
flask_port = flask_socket.getsockname()[1]
flask_socket.close()
print('BrainDir Uploader is running on port: ' + str(flask_port))


######################### Flask code #########################
# initialise app
flask_app = Flask(__name__, template_folder=templates_path, static_folder=static_path)

# config for flask-sijax
flask_app.config["CACHE_TYPE"] = "null"
flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
flask_sijax.Sijax(flask_app)


class SijaxHandler(object):
    @staticmethod
    def update_pgb(obj_response, up_prog_filename):
        upload_progress_file_path = os.path.join(appdata_path, 'files', up_prog_filename)
        with open(upload_progress_file_path, 'r+b') as upf:
                upload_prog_dict = json.load(upf)

        total_bytes = upload_prog_dict['total_bytes_to_upload']
        current_bytes = upload_prog_dict['bytes_uploaded']
        progress = current_bytes * 100 / total_bytes
        progress_str = str(progress) + '%'
        print(progress_str)

        obj_response.script(
            "$('#pgb1').width('" + progress_str + "');"
            "$('#pgb1-label').html('" + progress_str + "');"
        )

    @staticmethod
    def start_upload(obj_response, dir_to_upload_path, up_prog_filename):
        t = threading.Thread(target=main.start_upload, args=(dir_to_upload_path,
                                                             up_prog_filename,))
        t.start()

    @staticmethod
    def upload_complete(obj_response, up_prog_filename):
        upload_progress_file_path = os.path.join(appdata_path, 'files', up_prog_filename)
        with open(upload_progress_file_path, 'r+b') as upf:
                upload_prog_dict = json.load(upf)

        # remove upload progress log
        os.remove(upload_progress_file_path)

        remote_dir_path = upload_prog_dict['remote_dir_path_copy']
        obj_response.attr('#upload_location_field', 'value', remote_dir_path)

    @staticmethod
    def choose_dir_to_upload(obj_response):
        try:
            dir_path = MainWindow.display_dir_dialog()
        except:
            dir_path = ''
        obj_response.attr('#dir_to_upload_path_field', 'value', dir_path)

    @staticmethod
    def check_settings(obj_response):
        settings_file = os.path.join(appdata_path, 'files', 'settings.json')
        if os.path.isfile(settings_file):
            with open(settings_file, 'r+b') as sf:
                settings = json.load(sf)
            obj_response.attr('#hostname_field', 'value', settings['hostname'])
            obj_response.attr('#username_field', 'value', settings['username'])
            obj_response.attr('#host_save_path_field', 'value', settings['upload_save_path'])

        if os.path.isfile(os.path.join(appdata_path, 'keys', 'ssh_host_rsa_key.pub')):
            obj_response.script(
                "$('#load_hostkey_btn').removeClass('btn-default').addClass('btn-success');"
                "$('#load_hostkey_btn')"
                ".html('<span class=\"fa fa-check\"></span> Load new hostkey');"
            )

        if os.path.isfile(os.path.join(appdata_path, 'keys', 'braindir_rsa')):
            obj_response.script(
                "$('#generate_keys_btn').removeClass('btn-default').addClass('btn-success');"
                "$('#generate_keys_btn')"
                ".html('<span class=\"fa fa-check\"></span> Generate new public/private key pair');"
                "$('#generate_keys_btn').prop('disabled', false);"
            )

    @staticmethod
    def save_settings(obj_response, hostname, username, upload_save_path):
        settings = {'hostname': hostname,
                    'username': username,
                    'upload_save_path': upload_save_path}
        settings_file = os.path.join(appdata_path, 'files', 'settings.json')
        with open(settings_file, 'w+b') as sf:
            json.dump(settings, sf)

    @staticmethod
    def get_hostkey_fingerprint(obj_response, host):
        fingerprint = main.get_hostkey_fingerprint(host)
        obj_response.script(
            "$('#load_hostkey_btn').hide();"
            "$('#hostkey_alert').show();"
            "$('#hostkey_alert > h4').append($('#hostname_field').val());"
            "$('#hostkey_alert > span:eq(0)').append($('#hostname_field').val())"
            ".append(\" can't be established.\");"
            "$('#hostkey_alert > span:eq(1)').append('<strong>" + fingerprint + "</strong>');"
        )

    @staticmethod
    def load_hostkey(obj_response, host):
        main.load_hostkey(host)
        obj_response.script(
            "$('#hostkey_alert').hide();"
            "$('#load_hostkey_btn').show();"
            "$('#hostkey_alert > h4').html('Please verify the authenticity of host&nbsp;');"
            "$('#hostkey_alert > span:eq(0)').html('The authenticity of host&nbsp;');"
            "$('#hostkey_alert > span:eq(1)').html('RSA key fingerprint is&nbsp;');"
            "$('#load_hostkey_btn').removeClass('btn-default').addClass('btn-success');"
            "$('#load_hostkey_btn')"
            ".html('<span class=\"fa fa-check\"></span> Load new hostkey');"
        )

    @staticmethod
    def choose_public_key_save_path(obj_response):
        try:
            dir_path = MainWindow.display_dir_dialog()
        except:
            dir_path = ''
        obj_response.attr('#public_key_save_path', 'value', dir_path)

    @staticmethod
    def generate_keys(obj_response, save_path):
        if save_path == '':
            obj_response.script('alert("You must choose where to save your public key first!")')
        else:
            tr = threading.Thread(target=main.generate_keypair, args=(save_path,))
            tr.start()
            tr.join()
            obj_response.script(
                "$('#generate_keys_btn').removeClass('btn-default').addClass('btn-success');"
                "$('#generate_keys_btn')"
                ".html('<span class=\"fa fa-check\"></span> Generate new public/private key pair');"
                "$('#generate_keys_btn').prop('disabled', false);"
            )

    @staticmethod
    def display_resume_modal(obj_response):
        # generate list of interrupted uploads
        files_dir = os.path.join(appdata_path, 'files')
        files = os.listdir(files_dir)
        interrupted_uploads = [i for i in files if i.endswith('.up_prog.json')]

        # Hide nothing to resume message and show resume table if there are interrupted uploads
        if not interrupted_uploads == []:
            obj_response.script(
                "$('#nothing_to_resume').addClass('hidden');"
                "$('#resume_up_table').removeClass('hidden');"
            )

        for i, interrupted_upload in enumerate(interrupted_uploads):
            # get the pscid, dccid, visit label, and acquisition date of an interrupted upload
            basename = interrupted_upload.split('.', 1)[0]
            name_elements = basename.split('_')
            pscid = name_elements[0]
            dccid = name_elements[1]
            visit_label = name_elements[2]
            acquisition_date = name_elements[3]

            # get the percentage complete of an interrupted upload
            upload_progress_file_path = os.path.join(appdata_path, 'files', interrupted_upload)
            with open(upload_progress_file_path, 'r+b') as upf:
                upload_prog_dict = json.load(upf)
            total_bytes = upload_prog_dict['total_bytes_to_upload']
            current_bytes = upload_prog_dict['bytes_uploaded']
            progress = current_bytes * 100 / total_bytes
            progress_str = str(progress) + '%'

            # add a row to resume table with the above info
            obj_response.script(
                # add a row to the table
                "$('.resume_up_table_row').first().clone().removeClass('hidden')"
                ".attr('id', 'interrupted_up_" + str(i) + "').appendTo('#resume_up_table>tbody');"
                # enter pscid
                "$('#interrupted_up_" + str(i) + " .pscid').html('" + pscid + "');"
                # enter dccid
                "$('#interrupted_up_" + str(i) + " .dccid').html('" + dccid + "');"
                # enter visit label
                "$('#interrupted_up_" + str(i) + " .visit_label').html('" + visit_label + "');"
                # enter acquisition date
                "$('#interrupted_up_" + str(i) +
                " .acquisition_date').html('" + acquisition_date + "');"
                # set progress bar value
                "$('#interrupted_up_" + str(i) + " .progress-bar').width('" + progress_str + "');"
                "$('#interrupted_up_" + str(i) + " .progress-bar').html('" + progress_str + "');"
            )

    @staticmethod
    def delete_interrupted_up_log(obj_response, pscid, dccid, visit_label, acquisition_date):
        filename = ''.join(
            [pscid, '_', dccid, '_', visit_label, '_', acquisition_date, '.up_prog.json'])
        file_to_delete = os.path.join(appdata_path, 'files', filename)
        print(file_to_delete)
        os.remove(file_to_delete)

    @staticmethod
    def resume_upload(obj_response, pscid, dccid, visit_label, acquisition_date):
        filename = ''.join(
            [pscid, '_', dccid, '_', visit_label, '_', acquisition_date, '.up_prog.json'])
        upload_logfile = os.path.join(appdata_path, 'files', filename)

        # dir to upload path
        with open(upload_logfile, 'r+b') as upf:
                upload_prog_dict = json.load(upf)
        dir_to_upload_path = upload_prog_dict['local_dir_path']

        t = threading.Thread(target=main.upload_dir, args=(upload_logfile,))
        t.start()

        obj_response.attr('#dir_to_upload_path_field', 'value', dir_to_upload_path)
        obj_response.attr('#pscid_field', 'value', pscid)
        obj_response.attr('#dccid_field', 'value', dccid)
        obj_response.attr('#visit_label_field', 'value', visit_label)
        obj_response.attr('#acquisition_date_field', 'value', acquisition_date)


@flask_sijax.route(flask_app, '/')
def index():
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()

    return render_template('gui.html')


def start_server():
    http_server = WSGIServer(('', flask_port), flask_app)
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
        # comment out the following line to allow refresh for debugging
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
    url_to_display = QUrl('http://127.0.0.1:' + str(flask_port))
    browser = MainWindow(url_to_display)
    browser.show()
    browser.setFixedSize(890, 550)
    sys.exit(qt_app.exec_())


if __name__ == '__main__':
    display_webkit_window()