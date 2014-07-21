import paramiko
from scp import SCPClient
import os
import posixpath


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

    # load hostkey_file
    ssh.load_host_keys(hostkey_file)

    # establish an SSH connection to BDFS as user 'braindir'
    ssh.connect(host, username=username, pkey=key)

    # create scp object from paramiko transport
    scp = SCPClient(ssh.get_transport())

    # try uploading file
    try:
        scp.put(infile_path, outdir_remote_path)
        return True
    except:
        return False


def upload_dir(dir_to_upload, host, username, key_file, hostkey_file, pscid,
               dccid, visit_label, acquisition_date, task, run):
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

    # load key_file
    key = paramiko.RSAKey.from_private_key_file(key_file)

    ## Create new remote directory
    # create ssh object
    ssh = paramiko.SSHClient()

    # load hostkey_file
    ssh.load_host_keys(hostkey_file)

    # establish an SSH connection to BDFS as user 'braindir'
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
        print(upload_file(local_file_path, remote_file_path, host, username, key, hostkey_file))

    # close ssh client
    ssh.close()