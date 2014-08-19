"""
    main
    ----

    Implements the main, non-GUI related, application logic.

    Copyright (c) 2014 Jeremy Moreau.
    See LICENSE.txt for license information.

"""
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
    """Creates appdata directories if they don't yet exist.

    Args:
        path (str): Absolute path of directory where BrainDir Uploader should save appdata to. User
            must have permissions to read/write to this directory.

    :param path: str
    :return: none
    """
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
    """get the size of dir at dir_path recursively

    Args:
        dir_path (str): Absolute path of a directory

    Returns:
        int: The size in bytes of the directory and its contents.

    :param dir_path: str
    :return: int
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(dir_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)

            # skip over broken symlinks
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


def generate_upload_log(dir_to_upload, up_prog_filename):
    """Generate a JSON logfile describing files to upload.

    For a given directory to upload, generates a logfile which stores a number of variables
    describing the files to be uploaded into a dictionary which is then converted to JSON and saved
    in a file within the appdata/files/ directory of the appdata directory. The dictionary
    stores the following information:
    {
        'remote_dir_path': (str) Absolute path of the root directory where files will be uploaded to
            on the server. Once this directory has been created, the value is deleted.
        'remote_dir_path_copy': (str) A copy of the above variable.
        'local_dir_path': (str) Absolute path of the directory containing the files to be uploaded.
        'directories_to_create': (list) A list of the (str) absolute paths of the directories to be
            created on the server. Once a directory has been created, the value is deleted from the
            list.
        'files_to_upload': (list) A list of the (str) absolute paths of the files to be uploaded to
            the server. Once a file has been uploaded successfully, the value is deleted from the
            list.
        'files_to_upload_size': (list) A list of the (int) size in bytes ofe each file to be
            uploaded. The order of the list elements is the same as for the files_to_upload
            variable.
        'files_remote_path': (list) A list of the (str) absolute paths where the files to be
            uploaded should be uploaded to. The order of the list elements is the same as for the
            files_to_upload variable.
        'total_bytes_to_upload': (int) Total size in bytes of all the files to be uploaded.
        'bytes_uploaded': (int) Number of bytes uploaded up till now. This value is updated every
            time a file is successfully uploaded.
    }

    Args:
        dir_to_upload (str): Absolute path of the directory containing the files to upload.
        up_prog_filename (str): Filename to give to the JSON logfile. Basename will also be used as
            the name of the directory where the files will be uploaded to on the server.

    Returns:
        str: Absolute path of the JSON logfile.

    :param dir_to_upload: str
    :param up_prog_filename: str
    :return: str
    """
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
    """Connect to host listed in settings file.

    Opens settings.json file in appdata/files/ and reads the hostname of the server to connect to
    and the username of the user authenticating the connection. Loads the server's hostkey and the
    user's private key from within the appdata/keys/ directory. Once these data are loaded, attempts
    to connect to the server and returns a paramiko ssh object if the connection is established
    successfully.

    Returns:
        paramiko.client.SSHClient: A paramiko ssh object.

    :return: paramiko.client.SSHClient
    """
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
    """Upload a directory specified in an upload logfile.

    Establishes an SSH connection to the server specified in the settings file (appdata/
    settings.json), then opens an SFTP session and starts uploading a directory based on the
    information stored in an upload logfile. Starts by recreating the local directory hierarchy
    of the directory to upload on the server, then uploads each individual file. Once a directory
    is created or a file uploaded, its value is removed from the dictionary stored in the upload
    logfile to indicate that the creation/upload is complete. Once all directories and files have
    been created/uploaded, creates a directory on the server with the same name as the root upload
    directory, but with "_complete" appended at the end.

    Args:
        upload_prog_file_path (str): Absolute path of a JSON upload logfile describing a directory
            of data to be uploaded.

    :param upload_prog_file_path: str
    :return: none
    """
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
    """Upload a single file to a server.

    Args:
        local_file_path (str): Absolute path of a file to upload.
        remote_file_path (str): Absolute path of location on server file should be uploaded to.
        sftp (paramiko.sftp_client.SFTPClient): A paramiko SFTP client object

    Returns:
        bool: True if file was uploaded successfully, False otherwise.

    :param local_file_path: str
    :param remote_file_path: str
    :param sftp: paramiko.sftp_client.SFTPClient
    :return: bool
    """
    # try uploading file
    try:
        sftp.put(local_file_path, remote_file_path)
        return True
    except Exception, e:
        print(e)
        return False


#### SSH Authentification functions
def generate_keypair(public_key_save_path):
    """Generate a private/public key pair.

    Generates a 4096-bit RSA private/public key pair and saves them into appdata/keys/. Also saves a
    copy of the public key to a specified location.

    Args:
        public_key_save_path (str): Absolute path of location where to save a copy of the generated
            public key.

    :param public_key_save_path: str
    :return: none
    """
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
    """Get hostkey fingerprint of specified host.

    Args:
        host (str): IP address or hostname of a server.

    Returns:
        str: Hostkey fingerprint formatted with a colon every two characters.

    :param host: str
    :return: str
    """
    transport = paramiko.Transport(host)
    transport.start_client()
    hostkey = transport.get_remote_server_key()
    hostkey_md5 = hostkey.get_fingerprint()

    # format fingerprint with colons every two characters
    s = binascii.hexlify(hostkey_md5)
    fingerprint = ":".join(s[i:i+2] for i in range(0, len(s), 2))

    return fingerprint


def load_hostkey(host):
    """Write hostkey from a given host to appdata/keys/

    Args:
        host (str): IP address or hostname of a server.

    :param host: str
    :return: none
    """
    transport = paramiko.Transport(host)
    transport.start_client()
    hostkey = transport.get_remote_server_key()
    hostkey_txt = host + ' ' + hostkey.get_name() + ' ' + hostkey.get_base64()

    hostkey_file = os.path.join(appdata_path, 'keys', 'ssh_host_rsa_key.pub')
    with open(hostkey_file, 'w+b') as hf:
        hf.write(hostkey_txt)


def start_upload(dir_to_upload_path, up_prog_filename):
    """Wrapper function to generate an upload logfile and upload the associated directory.

    Args:
        dir_to_upload_path (str): Absolute path of directory to upload.
        up_prog_filename (str): Filename of upload progress logfile. Basename will also be used as
            the name of the directory where the files will be uploaded to on the server.

    :param dir_to_upload_path: str
    :param up_prog_filename: str
    :return: none
    """
    log_file = generate_upload_log(dir_to_upload_path, up_prog_filename)
    upload_dir(log_file)