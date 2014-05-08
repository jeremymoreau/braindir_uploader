import paramiko
from scp import SCPClient
import os
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
# functions and counter for progress bar

def get_size(dir_path):
	"""get the size of dir at dir_path recursively"""
	total_size = 0
	for dirpath, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			total_size += os.path.getsize(fp)
	return total_size

def compress(dir_path):
	"""adds dir at dir_path to tmp_archive.tar.gz in ./files/ and tracks operation progress"""
	# get basename of the directory to compress
	root_path = os.path.basename(dir_path)
	
	# set progress counter to 0
	progress_counter = 0
	
	# create empty archive in the ./files/ directory
	tar = tarfile.open(os.path.join(local_path,'files','tmp_archive.tar.gz'),'w:gz')
	
	# recursively add all files in the dir at dir_path to the empty archive
	# also track progress (which is why os.walk and convoluted code is used to loop over files)
	for dirpath, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			file_path = os.path.join(dirpath, f)

			path_split = file_path.partition(root_path)
			name_for_file = path_split[1] + path_split[2]

			tar.addfile(tarfile.TarInfo(name_for_file), file(file_path))
			
			
			# track progress of compression (!!! update the print to GUI display later !!!)	
			progress_counter += os.path.getsize(file_path)
			print(progress_counter)
	tar.close()
	

##### Encrypt the dir_to_upload with password_for_dir / decrypt






##### Testing
print(get_size(dir_to_upload))

compress(dir_to_upload)