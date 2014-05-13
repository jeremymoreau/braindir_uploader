import paramiko
from scp import SCPClient
import os
import tarfile
import Crypto
from time import time

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
			
			# skip over broken symlinks
			if os.path.exists(fp):
				total_size += os.path.getsize(fp)
	return total_size


##### tar and gzip the dir_to_upload / extract .tar.gz archive
def compress(dir_path):
	"""adds dir at dir_path to tmp_archive.tar.gz in ./files/ and tracks operation progress"""
	# get basename of the directory to compress
	root_path = os.path.basename(dir_path)
	
	# get total size of directory to compress
	dir_total_size = get_size(dir_path)
	
	# set progress counter to 0
	compress_progress_counter = 0
	
	# create empty archive in the ./files/ directory
	tar = tarfile.open(os.path.join(local_path,'files','tmp_archive.tar.gz'), 'w:gz')
	
	# recursively add all files in the dir at dir_path to the empty archive
	# also track progress (which is why os.walk and convoluted code is used to loop over files)
	for dirpath, dirnames, filenames in os.walk(dir_path):
		for f in filenames:
			file_path = os.path.join(dirpath, f)
			
			# skip over broken symlinks
			if not os.path.exists(file_path):
				continue
	
			# get the relative path of the file to add
			path_split = file_path.partition(root_path)
			name_for_file = path_split[1] + path_split[2]
			
			# generate tarinfo object for the file to add using the relative path
			# this avoids having the whole directory tree added to the archive
			file_tarinfo = tar.gettarinfo(name = file_path, arcname = name_for_file)
			
			# add file to archive
			tar.addfile(file_tarinfo, file(file_path))
			
			# track progress of compression
			compress_progress_counter += os.path.getsize(file_path)
			compress_progress = (compress_progress_counter * 100) / dir_total_size
			print('compression progress: ' + str(compress_progress)) # !!! update the print to GUI display later !!!
			
	tar.close()

	
def extract(archive_path, save_path):
	"""extract the archive at archive_path and save the extracted files at save_path"""
	# get total size of archive
	total_size = os.path.getsize(archive_path)
	
	# monitor extraction progress
	class MyFileObj(file):
		def read(self, size):
			extract_progress = (self.tell() * 100) / total_size
			print('extraction progress: ' + str(extract_progress)) # !!! update the print to GUI display later !!!
			return file.read(self, size)
	
	tar = tarfile.open(fileobj=MyFileObj(archive_path))
	
	# extract files at save_path
	tar.extractall(save_path)
	tar.close()


##### Split / concatenate files
def split_file(input_file, prefix, max_size = 5 * (10**7), buffer_size = 10**6):
	"""
	file: the input file
	prefix: prefix of the output files that will be created
	max_size: maximum size of each created file in bytes
	buffer_size: buffer_size size in bytes
	
	Returns the number of parts created.
	"""
	# track progress
	total_file_size = os.path.getsize(input_file)
	current_bytecount = 0
	
	with open(input_file, 'r+b') as src:
		suffix = 0
		while True:
			with open(prefix + '.%s' % suffix, 'w+b') as tgt:
				written = 0
				while written <= max_size:
					data = src.read(buffer_size)
					if data:
						tgt.write(data)
						written += buffer_size
						
						# track progress
						current_bytecount += buffer_size
						split_progress = (current_bytecount * 100) / total_file_size
						print('split progress: ' + str(split_progress)) # !!! update the print to GUI display later !!!
						
					else:
						return suffix
				suffix += 1

def cat_files(indir, outfile, buffer_size = 10**6):
	"""
	indir: directory containing files to concatenate
	outfile: the file that will be created
	buffer_size: buffer_size size in bytes
	"""
	# get list of files in indir, excluding hidden files starting with a dot
	infiles = [os.path.join(indir, x) for x in os.listdir(indir) if not x.startswith('.')]
	
	# track progress
	total_size = sum(os.path.getsize(x) for x in infiles)
	current_bytecount = 0
	
	with open(outfile, 'w+b') as tgt:
		for infile in sorted(infiles):
			with open(infile, 'r+b') as src:
				while True:
					data = src.read(buffer_size)
					if data:
						tgt.write(data)
						
						# track progress
						current_bytecount += buffer_size
						cat_progress = (current_bytecount * 100) / total_size
						print('concatenation progress: ' + str(cat_progress)) # !!! update the print to GUI display later !!!
					else:
						break


##### Generate SHA256 hash of infile and appends time() to generate a unique ID (BDID) for files
def generate_ID(infile):
	
	# generate SHA256 of file
	buffer_size = 10**6
	hasher = Crypto.Hash.SHA256.new()
	
	# track progress
	total_file_size = os.path.getsize(infile)
	current_bytecount = 0
	
	with open(infile, 'r+b') as f:
		data = f.read(buffer_size)
		while len(data) > 0:
			hasher.update(data)
			data = f.read(buffer_size)
			
			# track progress
			current_bytecount += buffer_size
			id_progress = (current_bytecount * 100) / total_file_size
			print('Hashing progress: ' + str(id_progress)) # !!! update the print to GUI display later !!!
			
	# create BDID
	BDID = hasher.hexdigest() + '_' + str(int(time()))
	
	return BDID

##### Encrypt the dir_to_upload with password_for_dir / decrypt






##### Testing

## compress
#compress(dir_to_upload)

## generate unique ID
#print(int(time()))
#print(generate_ID(os.path.join(local_path,'files','tmp_archive.tar.gz')))

## split
#split_file(os.path.join(local_path,'files','tmp_archive.tar.gz'), os.path.join(local_path,'files','split','part'))

## encrypt

## decrypt

## concatenate
#cat_files(os.path.join(local_path,'files','split'), os.path.join(local_path,'files','tmp_archive.tar.gz'))

## extract
#extract(os.path.join(local_path,'files','tmp_archive.tar.gz'), os.path.join(local_path,'files'))