import paramiko
from scp import SCPClient
import os
import tarfile
from time import sleep

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


##### General Functions
def get_size(dir_path):
	"""get the size of dir at dir_path recursively"""
	total_size = 0
	for dirpath, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			total_size += os.path.getsize(fp)
	return total_size


##### tar and gzip the dir_to_upload / extract .tar.gz archive
def compress(dir_path):
	"""adds dir at dir_path to tmp_archive.tar.gz in ./files/ and tracks operation progress"""
	# get basename of the directory to compress
	root_path = os.path.basename(dir_path)
	
	# set progress counter to 0
	compress_progress_counter = 0
	
	# create empty archive in the ./files/ directory
	tar = tarfile.open(os.path.join(local_path,'files','tmp_archive.tar.gz'), 'w:gz')
	
	# recursively add all files in the dir at dir_path to the empty archive
	# also track progress (which is why os.walk and convoluted code is used to loop over files)
	for dirpath, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			file_path = os.path.join(dirpath, f)

			# get the relative path of the file to add
			path_split = file_path.partition(root_path)
			name_for_file = path_split[1] + path_split[2]
			
			# generate tarinfo object for the file to add using the relative path
			# this avoids having the whole directory tree added to the archive
			file_tarinfo = tar.gettarinfo(name = file_path, arcname = name_for_file)
			
			# add file to archive
			tar.addfile(file_tarinfo, file(file_path))
			
			# get total size of directory to compress
			dir_total_size = get_size(dir_path)
			#print(dir_total_size)
			
			# track progress of compression	
			compress_progress_counter += os.path.getsize(file_path)
			#print(compress_progress_counter) # !!! update the print to GUI display later !!!
	
	tar.close()
	
def extract(archive_path):
	"""extract the archive at archive_path and save the extracted files at path_to_save"""
	# archive_size = os.path.getsize(archive_path)
	
	# open tar.gz archive
	tar = tarfile.open(os.path.join(local_path,'files','tmp_archive.tar.gz'),'r:gz')
	
	# get total size of uncompressed files
	size_of_extracted_archive = 0
	for f in tar.getmembers():
		size_of_extracted_archive += f.size
	print(size_of_extracted_archive)
	
	# track progress of extraction
	extract_progress_counter = 0
	# while (extract_progress_counter != size_of_extracted_archive)
	#	extract_progress_counter = 
	
	# extract all files 
	tar.extractall('./files/')
	tar.close()
		

##### Encrypt the dir_to_upload with password_for_dir / decrypt






##### Testing

## compress
print(get_size(dir_to_upload))
compress(dir_to_upload)

## extract
extract(os.path.join(local_path,'files','tmp_archive.tar.gz'))
