import paramiko
from scp import SCPClient
import os
from distutils import dir_util
import tarfile

##### General variables
local_path = os.path.realpath('.')

##### Stuff which will eventually be inputted through the GUI
# upload
dir_to_upload = '/Users/jeremymoreau/Desktop/testdir'
pass_encrypt = 'ipsum'

# download
id_of_dir_to_download = 'ipsum'
pass_decrypt = 'ipsum'
path_for_download = '/Users/jeremymoreau/Desktop/'


##### Connect to BDFS via SSH and enable SCP
ssh = paramiko.SSHClient()

# get path of user braindir's private key and load the key in the variable 'key'
key_file = os.path.join(local_path, 'keys','braindir_rsa')
key = paramiko.RSAKey.from_private_key_file(key_file)

# get the path of BDFS's hostkey and tell paramiko to accept BDFS as a known host
hostkey_file = os.path.join(local_path, 'keys','known_hosts')
ssh.load_host_keys(hostkey_file)

# establish an SSH connection to BDFS as user 'braindir'
#ssh.connect('bdfs.braindir.com', username='braindir', pkey=key)

# create scp object with which to use scp
#scp = SCPClient(ssh.get_transport())


##### tar and gzip the dir_to_upload / extract .tar.gz archive
def compress(dir_path):
	"copies dir at dir_path to ./files/ and adds dir to a tar.gz archive"
	name_of_dir = os.path.basename(dir_path)
	
	dir_util.copy_tree(dir_path, os.path.join(local_path,'files','tmp_upload_dir'))
	tar = tarfile.open(os.path.join(local_path,'files','tmp_archive_to_upload.tar.gz'),'w:gz')
	tar.add(os.path.join(local_path,'files','tmp_upload_dir'), arcname = name_of_dir)
	tar.close()
	

##### Encrypt the dir_to_upload with password_for_dir / decrypt






##### Testing
compress(dir_to_upload)