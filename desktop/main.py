import paramiko
from scp import SCPClient
import os
import tarfile
import time
from Crypto import Hash
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
import struct

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
def compress(dir_path, out_path, progress_log_path):
	"""adds dir at dir_path to tmp_archive.tar.gz in ./files/ and tracks operation progress"""
	# create blank progress file
	progress_file = open(progress_log_path, 'w+b')
	progress_file.write('00')
	progress_file.close()
	
	# get basename of the directory to compress
	root_path = os.path.basename(dir_path)
	
	# get total size of directory to compress
	dir_total_size = get_size(dir_path)
	
	# set progress counter to 0
	compress_progress_counter = 0
	
	# create empty archive in the ./files/ directory
	tar = tarfile.open(out_path, 'w:gz')
	
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
			progress_file = open(progress_log_path, 'w+b')
			progress_file.write('c' + str(compress_progress))
			progress_file.close()
			#print('compression progress: ' + str(compress_progress)) # !!! update the print to GUI display later !!!
			
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
def split_file(input_file, prefix, progress_log_path):
	"""
	file: the input file
	prefix: prefix of the output files that will be created
	max_size: maximum size of each created file in bytes
	buffer_size: buffer_size size in bytes
	
	Returns the number of parts created.
	"""
	max_size = 49000000
	buffer_size = 1000000
	
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
						progress_file = open(progress_log_path, 'w+b')
						progress_file.write('s' + str(split_progress))
						progress_file.close()
						#print('split progress: ' + str(split_progress)) # !!! update the print to GUI display later !!!
						
					else:
						os.remove(input_file)
						return suffix
				suffix += 1

def cat_files(indir, outfile, buffer_size = 1000000):
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
			os.remove(infile)


##### Generate SHA256 hash of infile and appends time.time() to generate a unique ID (BDID) for files
def generate_ID(infile, progress_log_path):
	
	# generate SHA256 of file
	buffer_size = 10**6
	hasher = Hash.SHA256.new()
	
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
			progress_file = open(progress_log_path, 'w+b')
			progress_file.write('i' + str(id_progress))
			progress_file.close()
			#print('Hashing progress: ' + str(id_progress)) # !!! update the print to GUI display later !!!
			
	# create BDID
	BDID = hasher.hexdigest() + '_' + str(int(time.time()))
	
	return BDID

##### Encrypt the dir_to_upload with password_for_dir / decrypt
def encrypt(indir, password, progress_log_path):
	
	# generate key from password
	#print('Generating key. . . (this should take about 10 seconds)') # !!! update the print to GUI display later !!!
	iterations = 100 # !!! change this values to 100000 later !!!
	key = ''
	salt = os.urandom(32)
	key = PBKDF2(password, salt, dkLen = 32, count = iterations)
	
	
	# get list of files in indir, excluding hidden files starting with a dot
	infiles = [os.path.join(indir, x) for x in os.listdir(indir) if not x.startswith('.')]
	
	# track progress
	total_file_count = len(infiles)
	encrypt_progress_counter = 0
	
	# encrypt files in indir using key and save them in the same directory
	chunksize = 64 * 1024
	for f in infiles:
		filesize = os.path.getsize(f)
		with open(f, 'r+b') as plaintext_file:
			out_filename = f + '.enc'
			iv = os.urandom(16)
			#print(out_filename)
			encryptor = AES.new(key, AES.MODE_CBC, iv)
			
			with open(out_filename, 'w+b') as ciphertext_file:
				ciphertext_file.write(struct.pack('<Q', filesize))
				ciphertext_file.write(iv)
				#print(iv.encode('hex'))
				#print(salt.encode('hex'))
				#print(key.encode('hex'))
				
				while True:
					chunk = plaintext_file.read(chunksize)
					if len(chunk) == 0:
						break
					elif len(chunk) % 16 != 0:
						chunk += ' ' * (16 - (len(chunk) % 16))
					
					ciphertext_file.write(encryptor.encrypt(chunk))
					
		# track progress
		encrypt_progress_counter += 1
		encrypt_progress = (encrypt_progress_counter * 100) / total_file_count
		progress_file = open(progress_log_path, 'w+b')
		progress_file.write('e' + str(encrypt_progress))
		progress_file.close()
		#print('Encryption progress: ' + str(encrypt_progress)) # !!! update the print to GUI display later !!!
		
		# remove plaintext file
		os.remove(f)
					
	# save salt in file
	salt_file = open(os.path.join(indir,'.salt'), 'w+b')
	salt_file.write(salt)
	salt_file.close()
					
def decrypt(indir, password):
	# get list of files in indir, excluding hidden files starting with a dot
	infiles = [os.path.join(indir, x) for x in os.listdir(indir) if not x.startswith('.')]
	
	# obtain key from password
	iterations = 100 # !!! change this values to 100000 later !!!
	salt = open(os.path.join(indir,'.salt'), 'r+b').read()
	key = PBKDF2(password, salt, dkLen = 32, count = iterations)
	print(key.encode('hex'))	
	
	# track progress
	total_file_count = len(infiles)
	decrypt_progress_counter = 0
	
	# decrypt files in indir using key and save them in the same directory
	chunksize = 64 * 1024
	for f in infiles:
		out_filename = os.path.splitext(f)[0]
		with open(f, 'r+b') as ciphertext_file:
			origsize = struct.unpack('<Q', ciphertext_file.read(struct.calcsize('Q')))[0]
			iv = ciphertext_file.read(16)
			decryptor = AES.new(key, AES.MODE_CBC, iv)
			
			with open(out_filename, 'w+b') as plaintext_file:
				while True:
					chunk = ciphertext_file.read(chunksize)
					if len(chunk) == 0:
						break
					plaintext_file.write(decryptor.decrypt(chunk))
				plaintext_file.truncate(origsize)
		
		# track progress
		decrypt_progress_counter += 1
		decrypt_progress = (decrypt_progress_counter * 100) / total_file_count
		print('Decryption progress: ' + str(decrypt_progress)) # !!! update the print to GUI display later !!!
		
		# remove ciphertext file
		os.remove(f)



def upload_private(dir_to_upload, passphrase):
	tmp_archive_path = os.path.join(local_path,'files','tmp_archive.tar.gz')
	progress_log_path = os.path.join(local_path,'files','.progress_file.txt')
	
	compress(dir_to_upload, tmp_archive_path, progress_log_path)
	archive_id = generate_ID(tmp_archive_path, progress_log_path)
	os.rename(tmp_archive_path, os.path.join(local_path,'files', archive_id + '.tar.gz'))
	os.mkdir(os.path.join(local_path,'files', archive_id))
	split_file(os.path.join(local_path,'files', archive_id + '.tar.gz'), os.path.join(local_path,'files', archive_id, archive_id), progress_log_path)
	encrypt(os.path.join(local_path,'files', archive_id), passphrase, progress_log_path)
	
##### Testing
# upload_private
#upload_private('/Users/jeremymoreau/Desktop/testdir', 'this is not a good password')

## compress
#compress(dir_to_upload)

## generate unique ID
#print(int(time()))
#print(generate_ID(os.path.join(local_path,'files','tmp_archive.tar.gz')))

## split
#split_file(os.path.join(local_path,'files','tmp_archive.tar.gz'), os.path.join(local_path,'files','split','part'))

## encrypt
#encrypt(os.path.join(local_path,'files','split'), 'this is not a good password')

## decrypt
#decrypt(os.path.join(local_path,'files','split'), 'this is not a good password')

## concatenate
#cat_files(os.path.join(local_path,'files','split'), os.path.join(local_path,'files','tmp_archive.tar.gz'))

## extract
#extract(os.path.join(local_path,'files','tmp_archive.tar.gz'), os.path.join(local_path,'files'))