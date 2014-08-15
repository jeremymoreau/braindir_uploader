from cx_Freeze import setup, Executable
import os


def generate_include_list(root_dir):
    file_list = []

    for directory, directories, files in os.walk(root_dir):
        for filename in files:
            rel_dir = os.path.relpath(directory, root_dir)
            rel_file = os.path.join(rel_dir, filename)
            file_list.append(rel_file)

    file_list = [x for x in file_list if not '.DS_Store' in x and
                 (x.startswith('static') or x.startswith('templates'))]
    return file_list


build_dir = os.path.join(os.path.realpath('.'))

includefiles = generate_include_list(build_dir)
packages = ['flask', 'flask_sijax', 'jinja2', 'gevent', 'paramiko']
qt_menu_nib_path = os.path.join(os.path.expanduser('~'), 'Qt', '5.3', 'Src', 'qtbase', 'src',
                                'plugins', 'platforms', 'cocoa')

setup(
name = 'braindir_uploader',
version = '0.1.0',
description = 'A neuroimaging data upload client for LORIS',
author = 'Jeremy Moreau',
author_email = 'mail@jeremymoreau.com',
options = {'build_exe': {'include_files':includefiles, 'packages':packages, 'excludes':['tkinter']},
           'bdist_mac': {'qt_menu_nib':qt_menu_nib_path,
                         'iconfile':'icons/braindir_uploader_icon.icns',
                         'bundle_name':'BrainDir Uploader'}},
py_modules=['main', 'braindir_uploader'],
executables = [Executable(script='braindir_uploader.py')]
)