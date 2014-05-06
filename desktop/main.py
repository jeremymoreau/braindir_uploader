import paramiko
from scp import SCPClient
import os, sys

ssh = paramiko.SSHClient()

# get path of user braindir's private key and load the key in the variable 'key'
key_file = os.path.join(os.path.realpath('..'),'desktop', 'keys','braindir_rsa')
key = paramiko.RSAKey.from_private_key_file(key_file)

# get the path of BDSS's hostkey and tell paramiko to accept BDSS as a known host
hostkey_file = os.path.join(os.path.realpath('..'),'desktop', 'keys','known_hosts')
ssh.load_host_keys(hostkey_file)

# establish an SSH connection to BDSS as user 'braindir'
ssh.connect('108.61.191.58', username='braindir', pkey=key)

# create scp object with which to use scp
scp = SCPClient(ssh.get_transport())
