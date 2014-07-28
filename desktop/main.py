import paramiko
from scp import SCPClient
import os
import shutil
import posixpath
import json
import binascii


######################### General variables #########################
local_path = os.path.realpath('.')


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


def upload_file(infile_path, outdir_remote_path, host, username, key,
                hostkey_file):
    # create ssh object
    ssh = paramiko.SSHClient()

    # load server's public key file
    ssh.load_host_keys(hostkey_file)

    # establish an SSH connection to storage server
    ssh.connect(host, username=username, pkey=key)

    # create scp object from paramiko transport
    scp = SCPClient(ssh.get_transport())

    # try uploading file
    try:
        scp.put(infile_path, outdir_remote_path)
        return True
    except:
        return False


def generate_upload_list(dir_to_upload, pscid, dccid, visit_label, acquisition_date):
    directories_to_create = []
    files_to_upload = []
    files_to_upload_size = []
    files_remote_path = []

    # check for settings.json file and load it if it exists
    settings_file = os.path.join(local_path, 'files', 'settings.json')
    if os.path.isfile(settings_file):
            with open(settings_file, 'r+b') as sf:
                settings = json.load(sf)
    else:
        settings = {}

    # set the upload root directory
    if not settings == {}:
        root_dir = settings['upload_save_path']
    else:
        root_dir = '.'

    # construct the path of the remote dir where files are to be uploaded
    remote_dir_path = ''.join(
        [root_dir,  pscid, '_', str(dccid), '_' + visit_label, '_', str(acquisition_date)])

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
    upload_list = {
        'remote_dir_path': remote_dir_path,
        'directories_to_create': directories_to_create,
        'files_to_upload': files_to_upload,
        'files_to_upload_size': files_to_upload_size,
        'files_remote_path': files_remote_path,
        'total_bytes_to_upload': total_bytes_to_upload,
        'bytes_uploaded': 0
    }

    # save the dictionary in a json file
    upload_filename = os.path.basename(os.path.normpath(remote_dir_path)) + '.uploadprog.json'
    upload_progress_file = os.path.join(local_path, 'files', upload_filename)
    with open(upload_progress_file, 'w+b') as upf:
            json.dump(upload_list, upf)

#generate_upload_list('/Users/jeremymoreau/Desktop/brainz', 'DCC9999', '123456', 'V01', '20140728')


# def upload_dir(dir_to_upload, pscid, dccid, visit_label, acquisition_date):
#     # load hostname and username from settings.json
#     settings_file = os.path.join(local_path, 'files', 'settings.json')
#     with open(settings_file, 'r+b') as sf:
#         settings = json.load(sf)
#     host = settings['hostname']
#     username = settings['username']
#
#     # set path of client's private key file and server's public key file
#     client_prv_key_file_path = os.path.join(local_path, 'keys', 'braindir_rsa')
#     server_pub_key_file_path = os.path.join(local_path, 'keys', 'braindir_server_rsa.pub')
#
#
#
#     # load client's private key file
#     key = paramiko.RSAKey.from_private_key_file(client_prv_key_file_path)
#
#     ## Create new remote directory
#     # create ssh object
#     ssh = paramiko.SSHClient()
#
#     # load server's public key file
#     ssh.load_host_keys(server_pub_key_file_path)
#
#     # establish an SSH connection to storage server
#     ssh.connect(host, username=username, pkey=key)
#
#     # open an sftp session
#     sftp = ssh.open_sftp()
#
#     # create remote directory
#     sftp.mkdir(remote_dir_name, mode=0750)
#
#     # create remote subdirectories
#     for d in directories_to_create:
#         sftp.mkdir(d, mode=0750)
#
#     # copy files to server
#     for i in range(0, len(files_to_upload)):
#         local_file_path = files_to_upload[i]
#         remote_file_path = files_remote_path[i]
#
#         # test if file was uploaded correctly
#         print(upload_file(local_file_path, remote_file_path, host, username, key, server_pub_key_file_path))
#
#     # close ssh client
#     ssh.close()


#### SSH Authentification functions
def generate_keypair(public_key_save_path):
    print(public_key_save_path)
    private_key = paramiko.RSAKey.generate(4096)
    private_key.write_private_key_file(os.path.join(local_path, 'keys', 'braindir_rsa'))
    public_key = 'ssh-rsa ' + private_key.get_base64()
    public_key_tmp_path = os.path.join(local_path, 'keys', 'braindir_rsa.pub')
    public_key_file = open(public_key_tmp_path, 'w+b')
    public_key_file.write(public_key)
    public_key_file.close()
    print(public_key_tmp_path)
    print(public_key_save_path)
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

    hostkey_file = os.path.join(local_path, 'keys', 'ssh_host_rsa_key.pub')
    with open(hostkey_file, 'w+b') as hf:
        hf.write(hostkey_txt)

#load_hostkey('192.168.201.101')

#generate_keypair('/Users/jeremymoreau/Desktop/')
#upload_dir('/Users/jeremymoreau/Desktop/brainz', 'DCC9999', '123456', 'V01', '20140723')

# # set path of client's private key file and server's public key file
# client_prv_key_file_path = os.path.join(local_path, 'keys', 'braindir_rsa')
# server_pub_key_file_path = os.path.join(local_path, 'keys', 'ssh_host_rsa_key.pub')
# # load client's private key file
# key = paramiko.RSAKey.from_private_key_file(client_prv_key_file_path)
#
# # create ssh object
# ssh = paramiko.SSHClient()
#
# ssh.load_host_keys(server_pub_key_file_path)
#
# # establish an SSH connection to storage server
# ssh.connect('192.168.201.101', username='testuser', pkey=key)
#
# # open an sftp session
# #sftp = ssh.open_sftp()
# #print(sftp.listdir('.'))