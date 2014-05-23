# -*- coding: utf-8 -*-

import main
import os
from flask import Flask, g, render_template, request, redirect
import flask_sijax

progress_bar_value = '95%'

# LOCAL_FILE_STORAGE_DIR = os.path.join(os.path.realpath('.'), 'files')
# print(LOCAL_FILE_STORAGE_DIR)

# initialise app
app = Flask(__name__)

# config for flask-sijax
app.config["SIJAX_STATIC_PATH"] = os.path.join(main.local_path, 'static', 'js', 'sijax')
flask_sijax.Sijax(app)

class SijaxHandler(object):
	@staticmethod
	def set_progress(obj_response):
		obj_response.css('.progress-bar', 'width', progress_bar_value)
		obj_response.html('.progress-bar-label',progress_bar_value)

@flask_sijax.route(app, '/')
def index():
	if g.sijax.is_sijax_request:
		g.sijax.register_object(SijaxHandler)
		return g.sijax.process_request()
	
	return render_template('view_1.html')

if __name__ == '__main__':
	app.run(debug=True)