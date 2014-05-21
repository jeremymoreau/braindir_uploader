import main
import os
from flask import Flask, render_template
from flask import request, redirect

LOCAL_FILE_STORAGE_DIR = os.path.join(os.path.realpath('.'), 'files')
print(LOCAL_FILE_STORAGE_DIR)

app = Flask(__name__)

@app.route('/')
def view_1():
	return render_template('view_1.html')

@app.route('/view_1_actions', methods = ['POST'])
def view_1_actions():
    dir_to_upload = request.files.getlist('dir_to_upload')
    #filename = dir_to_upload.filename
    #dir_to_upload.save(os.path.join(LOCAL_FILE_STORAGE_DIR, filename))
    print(dir_to_upload)
    return redirect('/')
    
# @app.route('/emails')
# def emails():
#     return render_template('emails.html', email_addresses=email_addresses)

if __name__ == '__main__':
	app.run(debug=True)