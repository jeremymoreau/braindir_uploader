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


def upload_dir(dir_to_upload, pscid, dccid, visit_label, acquisition_date):
    # load hostname and username from settings.json
    settings_file = os.path.join(local_path, 'files', 'settings.json')
    with open(settings_file, 'r+b') as sf:
        settings = json.load(sf)
    host = settings['hostname']
    username = settings['username']

    # set path of client's private key file and server's public key file
    client_prv_key_file_path = os.path.join(local_path, 'keys', 'braindir_rsa')
    server_pub_key_file_path = os.path.join(local_path, 'keys', 'braindir_server_rsa.pub')

    # get name of remote dir where files are to be uploaded
    remote_dir_name = ''.join(
        [pscid, '_', str(dccid), '_' + visit_label, '_', str(acquisition_date)])

    # create list of files to upload and directories to create
    directories_to_create = []
    files_to_upload = []
    files_remote_path = []

    for dirname, dirnames, filenames in os.walk(dir_to_upload):
        for subdirname in dirnames:
            directory = posixpath.join(
                remote_dir_name, posixpath.relpath(
                    posixpath.join(dirname, subdirname), dir_to_upload))
            directories_to_create.append(directory)
        for filename in filenames:
            file_to_upload = os.path.join(dirname, filename)
            files_to_upload.append(file_to_upload)

            remote_file_path = posixpath.join(
                remote_dir_name, posixpath.relpath(
                    posixpath.join(dirname, filename), dir_to_upload))
            files_remote_path.append(remote_file_path)

    print(directories_to_create)
    print(files_to_upload)
    print(files_remote_path)

    # load client's private key file
    key = paramiko.RSAKey.from_private_key_file(client_prv_key_file_path)

    ## Create new remote directory
    # create ssh object
    ssh = paramiko.SSHClient()

    # load server's public key file
    ssh.load_host_keys(server_pub_key_file_path)

    # establish an SSH connection to storage server
    ssh.connect(host, username=username, pkey=key)

    # open an sftp session
    sftp = ssh.open_sftp()

    # create remote directory
    sftp.mkdir(remote_dir_name, mode=0750)

    # create remote subdirectories
    for d in directories_to_create:
        sftp.mkdir(d, mode=0750)

    # copy files to server
    for i in range(0, len(files_to_upload)):
        local_file_path = files_to_upload[i]
        remote_file_path = files_remote_path[i]

        # test if file was uploaded correctly
        print(upload_file(local_file_path, remote_file_path, host, username, key, server_pub_key_file_path))

    # close ssh client
    ssh.close()


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


#generate_keypair('/Users/jeremymoreau/Desktop/')
#upload_dir('/Users/jeremymoreau/Desktop/brainz', 'DCC9999', '123456', 'V01', '20140723')

# # set path of client's private key file and server's public key file
# client_prv_key_file_path = os.path.join(local_path, 'keys', 'braindir_rsa')
# server_pub_key_file_path = os.path.join(local_path, 'keys', 'braindir_server_rsa.pub')
# # load client's private key file
# key = paramiko.RSAKey.from_private_key_file(client_prv_key_file_path)
#
# # create ssh object
# ssh = paramiko.SSHClient()
#
# t = paramiko.Transport('192.168.201.101')
# t.start_client()
# import binascii
# hostkey = t.get_remote_server_key()
# print(hostkey.get_base64())
# md5 = hostkey.get_fingerprint()
# s = binascii.hexlify(md5)
# print(":".join(s[i:i+2] for i in range(0, len(s), 2)))


#paramiko.Transport.get_remote_server_key()
# # load server's public key file
# hostkey = paramiko.HostKeys()
# hostkey.load(server_pub_key_file_path)
# print(hostkey.has_key())
#ssh.load_host_keys(server_pub_key_file_path)
#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# establish an SSH connection to storage server
#ssh.connect('192.168.201.101', username='testuser', pkey=key)

# open an sftp session
#sftp = ssh.open_sftp()
#print(get_hostkey_fingerprint('192.168.201.101'))