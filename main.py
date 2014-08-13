import paramiko
import os
import shutil
import posixpath
import json
import binascii
import copy
import sys


######################### Set up data directories #########################
# create appdata directories if they don't yet exist
def check_for_datadirs(path):
    if not os.path.isdir(path):
        os.mkdir(path, 0755)

    files_dir = os.path.join(path, 'files')
    if not os.path.isdir(files_dir):
        os.mkdir(files_dir, 0755)

    keys_dir = os.path.join(path, 'keys')
    if not os.path.isdir(keys_dir):
        os.mkdir(keys_dir, 0755)

# Set appdata directory root for each platform
if sys.platform.startswith('linux'):
    appdata_path = os.path.join(os.path.expanduser('~'), '.braindir_uploader')
    check_for_datadirs(appdata_path)
elif sys.platform == "darwin":
    appdata_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support',
                                'braindir_uploader')
    check_for_datadirs(appdata_path)

######################### General Functions #########################
def get_size(dir_path):
    """get the size of dir at dir_path recursively"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)

            # skip over broken symlinks
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


def generate_upload_log(dir_to_upload, up_prog_filename):
    directories_to_create = []
    files_to_upload = []
    files_to_upload_size = []
    files_remote_path = []

    # Get the value of upload_save_path from settings.json if the file exists
    settings_file = os.path.join(appdata_path, 'files', 'settings.json')
    if os.path.isfile(settings_file):
            with open(settings_file, 'r+b') as sf:
                settings = json.load(sf)
            upload_save_path = settings['upload_save_path']
    else:
        upload_save_path = ''

    # set the upload root directory
    if not upload_save_path == '':
        root_dir = upload_save_path
    else:
        root_dir = './'

    # construct the path of the remote dir where files are to be uploaded
    remote_dir_name = up_prog_filename.split('.', 1)[0]
    remote_dir_path = posixpath.join(root_dir, remote_dir_name)
    print('remote_dir_path: ' + remote_dir_path)

    # generate lists of directories to create, files to upload, and corresponding remote file paths
    for dirname, dirnames, filenames in os.walk(dir_to_upload):
        for subdirname in dirnames:
            directory = posixpath.join(
                remote_dir_path, posixpath.relpath(
                    posixpath.join(dirname, subdirname), dir_to_upload))
            directories_to_create.append(directory)
        for filename in filenames:
            file_to_upload = os.path.join(dirname, filename)
            files_to_upload.append(file_to_upload)

            file_to_upload_size = os.path.getsize(file_to_upload)
            files_to_upload_size.append(file_to_upload_size)

            remote_file_path = posixpath.join(
                remote_dir_path, posixpath.relpath(
                    posixpath.join(dirname, filename), dir_to_upload))
            files_remote_path.append(remote_file_path)

    # calculate total bytes to upload
    total_bytes_to_upload = sum(files_to_upload_size)

    # store all above information in a dictionary
    upload_prog_dict = {
        'remote_dir_path': remote_dir_path,
        'remote_dir_path_copy': remote_dir_path,
        'local_dir_path': dir_to_upload,
        'directories_to_create': directories_to_create,
        'files_to_upload': files_to_upload,
        'files_to_upload_size': files_to_upload_size,
        'files_remote_path': files_remote_path,
        'total_bytes_to_upload': total_bytes_to_upload,
        'bytes_uploaded': 0
    }

    # save the dictionary in a json file
    upload_filename = os.path.basename(os.path.normpath(remote_dir_path)) + '.up_prog.json'
    upload_progress_file_path = os.path.join(appdata_path, 'files', upload_filename)
    with open(upload_progress_file_path, 'w+b') as upf:
            json.dump(upload_prog_dict, upf)

    return upload_progress_file_path


def connect_to_host():
    # load hostname and username from settings.json
    settings_file = os.path.join(appdata_path, 'files', 'settings.json')
    with open(settings_file, 'r+b') as sf:
        settings = json.load(sf)
    host = settings['hostname']
    username = settings['username']

    # set path of client's private key file and the hostkey
    client_prv_key_file_path = os.path.join(appdata_path, 'keys', 'braindir_rsa')
    hostkey_file_path = os.path.join(appdata_path, 'keys', 'ssh_host_rsa_key.pub')

    # load client's private key file
    key = paramiko.RSAKey.from_private_key_file(client_prv_key_file_path)

     # create ssh object
    ssh = paramiko.SSHClient()

    # load hostkey
    ssh.load_host_keys(hostkey_file_path)

    # establish an SSH connection to storage server
    ssh.connect(host, username=username, pkey=key)

    return ssh


def upload_dir(upload_prog_file_path):
    # load upload progress file and make a copy
    with open(upload_prog_file_path, 'r+b') as upf:
        upload_prog_dict = json.load(upf)
    upload_prog_dict_copy = copy.deepcopy(upload_prog_dict)

    # connect to host
    ssh = connect_to_host()

    # open an sftp session
    sftp = ssh.open_sftp()

    # create remote root directory if it hasn't been created yet
    remote_dir = upload_prog_dict_copy['remote_dir_path']
    if not remote_dir == '':
        sftp.mkdir(remote_dir)

        # update progress log
        upload_prog_dict['remote_dir_path'] = ''
        with open(upload_prog_file_path, 'w+b') as upf:
            json.dump(upload_prog_dict, upf)

    #create remote subdirectories if they haven't been created yet
    directories_to_create = upload_prog_dict_copy['directories_to_create']
    if not directories_to_create == []:
        #print(directories_to_create)
        for directory in directories_to_create:
            #print('creating: ' + directory)
            #print(directories_to_create)
            sftp.mkdir(directory)

            # update progress log
            upload_prog_dict['directories_to_create'].remove(directory)
            with open(upload_prog_file_path, 'w+b') as upf:
                json.dump(upload_prog_dict, upf)

    # upload files to server if they haven't been uploaded yet
    files_to_upload = upload_prog_dict_copy['files_to_upload']
    #print(files_to_upload)
    files_remote_path = upload_prog_dict_copy['files_remote_path']
    files_to_upload_size = upload_prog_dict_copy['files_to_upload_size']
    for i in range(0, len(files_to_upload)):
        local_file_path = files_to_upload[i]
        remote_file_path = files_remote_path[i]
        file_size = files_to_upload_size[i]

        # upload individual files (try three times)
        for attempt in range(3):
            try:
                #print(local_file_path)
                #print(remote_file_path)
                file_uploaded = upload_file(local_file_path, remote_file_path, sftp)
                if file_uploaded:
                    upload_prog_dict['bytes_uploaded'] += file_size
                    #print(upload_prog_dict['bytes_uploaded'])
                    upload_prog_dict['files_to_upload'].remove(local_file_path)
                    upload_prog_dict['files_remote_path'].remove(remote_file_path)
                    upload_prog_dict['files_to_upload_size'].remove(file_size)
                    with open(upload_prog_file_path, 'w+b') as upf:
                        json.dump(upload_prog_dict, upf)
                    break
            except Exception, e:
                print(e)

            if attempt == 2:
                print('Upload Interrupted!')

    # create "_complete" dir on host to signal that upload is complete
    complete_dir_name = upload_prog_dict_copy['remote_dir_path_copy'] + '_complete'
    sftp.mkdir(complete_dir_name)

    # close ssh client
    ssh.close()


def upload_file(local_file_path, remote_file_path, sftp):

    # try uploading file
    try:
        sftp.put(local_file_path, remote_file_path)
        return True
    except Exception, e:
        print(e)
        return False


#### SSH Authentification functions
def generate_keypair(public_key_save_path):
    #print(public_key_save_path)
    private_key = paramiko.RSAKey.generate(4096)
    private_key.write_private_key_file(os.path.join(appdata_path, 'keys', 'braindir_rsa'))
    public_key = 'ssh-rsa ' + private_key.get_base64()
    public_key_tmp_path = os.path.join(appdata_path, 'keys', 'braindir_rsa.pub')
    public_key_file = open(public_key_tmp_path, 'w+b')
    public_key_file.write(public_key)
    public_key_file.close()
    #print(public_key_tmp_path)
    #print(public_key_save_path)
    shutil.copy(public_key_tmp_path, public_key_save_path)


def get_hostkey_fingerprint(host):
    transport = paramiko.Transport(host)
    transport.start_client()
    hostkey = transport.get_remote_server_key()
    hostkey_md5 = hostkey.get_fingerprint()

    # format fingerprint with colons every two characters
    s = binascii.hexlify(hostkey_md5)
    fingerprint = ":".join(s[i:i+2] for i in range(0, len(s), 2))

    return fingerprint


def load_hostkey(host):
    transport = paramiko.Transport(host)
    transport.start_client()
    hostkey = transport.get_remote_server_key()
    hostkey_txt = host + ' ' + hostkey.get_name() + ' ' + hostkey.get_base64()

    hostkey_file = os.path.join(appdata_path, 'keys', 'ssh_host_rsa_key.pub')
    with open(hostkey_file, 'w+b') as hf:
        hf.write(hostkey_txt)


def start_upload(dir_to_upload_path, up_prog_filename):
    log_file = generate_upload_log(dir_to_upload_path, up_prog_filename)
    upload_dir(log_file)