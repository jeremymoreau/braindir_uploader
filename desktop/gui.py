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
		try:
			progress_file = open(os.path.join(local_path,'files','.progress_file.txt'), 'r+b')
			progress_file_text = progress_file.read()
			progress_file.close()
			
			print(progress_file_text)
			progress_bar_value = progress_file_text[1:] + '%'
			
			if progress_file_text[0] == 'c':
				print('compressing...')
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
			elif progress_file_text == '':
				print('no progress')
				obj_response.html('#progress_state', '')
				progress_bar_value = 0	
				obj_response.css('.progress-bar', 'width', progress_bar_value)
				obj_response.html('.progress-bar-label', progress_bar_value)	
		except:
			pass
			
		
	@staticmethod
	def start_upload(obj_response, dir_to_upload_path, passphrase):
		t = threading.Thread(target=main.upload_private, args=(dir_to_upload_path, passphrase,))
		t.start()

@flask_sijax.route(app, '/')
def index():
	if g.sijax.is_sijax_request:
		g.sijax.register_object(SijaxHandler)
		return g.sijax.process_request()
	
	return render_template('view_1.html')

if __name__ == '__main__':
	app.run(debug=True)