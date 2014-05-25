# -*- coding: utf-8 -*-

import main
import os
from flask import Flask, g, render_template, request, redirect
import flask_sijax
import threading

##### General variables
local_path = os.path.realpath('.')
dir_to_upload = '/Users/jeremymoreau/Desktop/testdir'
#progress_bar_value = str(90) + '%'

# LOCAL_FILE_STORAGE_DIR = os.path.join(os.path.realpath('.'), 'files')
# print(LOCAL_FILE_STORAGE_DIR)

# initialise app
app = Flask(__name__)

# config for flask-sijax
app.config["CACHE_TYPE"] = "null"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["SIJAX_STATIC_PATH"] = os.path.join(main.local_path, 'static', 'js', 'sijax')
flask_sijax.Sijax(app)

class SijaxHandler(object):
	@staticmethod
	def set_progress(obj_response):
		progress_file = open(os.path.join(local_path,'files','.progress_file.txt'), 'r+b')
		progress_bar_value = progress_file.read() + '%'
		obj_response.css('.progress-bar', 'width', progress_bar_value)
		obj_response.html('.progress-bar-label',progress_bar_value)
		
	@staticmethod
	def start_upload(obj_response, file_to_upload_path):
		print(file_to_upload_path)
		#t = threading.Thread(target=main.compress, args=(dir_to_upload,))
		#t.start()

@flask_sijax.route(app, '/')
def index():
	if g.sijax.is_sijax_request:
		g.sijax.register_object(SijaxHandler)
		return g.sijax.process_request()
	
	return render_template('view_1.html')

if __name__ == '__main__':
	app.run(debug=True)