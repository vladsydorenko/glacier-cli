#!/usr/local/bin/python
from boto.utils import parse_ts
from boto.glacier import connect_to_region
from boto.glacier.layer2 import Layer2
from boto.glacier.exceptions import UploadArchiveError
from datetime import date
import zipfile
import sys
import os
import json
import datetime
import time
import argparse

# Outputs the config file
def write_config_file():
	with open(config, 'w') as f:
		f.write(access_key_id + "\n")
		f.write(secret_key + "\n")
		f.write(vault_name + '|' + region + "\n")
		f.write('|'.join(dirs) + "\n")
		f.write(inventory_job + "\n")
		f.write(ls_present + "\n")
		for name, data in ls.iteritems():
			f.write(name + '|' + str(data['id']) + '|' + str(data['size']) + "\n")

def format_bytes(bytes):
	for x in ['bytes', 'KB', 'MB', 'GB']:
		if bytes < 1024.0:
			return "%3.1f %s" % (bytes, x)
		bytes /= 1024.0
	return "%3.1f %s" % (bytes, 'TB')
	
def format_time(num):
	times = []
	for x in [(60, 'second'), (60, 'minute'), (1e10, 'hour')]:
		if num % x[0] >= 1:
			times.append('%d %s%s' % (num % x[0], x[1], 's' if num % x[0] != 1 else ''))
		num /= x[0]
	times.reverse()
	return ', '.join(times)

def zipdir(path, ziph):
	# ziph is zipfile handle
	for root, dirs, files in os.walk(path):
		for file in files:
			print " Adding: " + root + os.sep + file
			ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))

def generate_archive_name(dir):
	split_dir = dir.split('/')
	name = date.today().strftime("%d_%m_%Y") + "__" + split_dir[-1] + ".zip";
	return name

config = "config_nongit.f"	
# Make sure the config file exists
if not os.path.exists(config):
	print "Config file not found. Pass in a file with the vault name and the directory to sync on separate lines."
	sys.exit(1)

# Read the config file
with open(config, 'rU') as f:
	access_key_id = f.readline().strip()
	secret_key = f.readline().strip()

	vault_info = f.readline().strip().split('|')
	vault_name = vault_info[0]
	region 	   = vault_info[1]
	
	dirs = f.readline().strip().split('|')
	inventory_job = f.readline().strip()
	ls_present = f.readline().strip()

	
	ls = {}
	for file in f.readlines():
		name, id, size = file.strip().split('|')
		ls[name] = {
			'id': id,
			'size': int(size)
		}

if len(sys.argv) < 2:
	print r"You need to give a job specifier e.g. -b or -dv or etc."
	sys.exit(1)

parser = argparse.ArgumentParser(description='Command line interface for Amazon Glacier')
parser.add_argument('-c','--create', help='Create new vault', action="store_true")
parser.add_argument('-dv','--delete', help='Delete vault', action="store_true")
parser.add_argument('-b','--backup', help='Immediately backup data', action="store_true")
arg = parser.parse_args()

# Check some of the values in the config file
if not access_key_id or not secret_key:
	print "You need to give an access key and secret key to get access."
	sys.exit(1)

if not vault_name:
	print "You need to give a vault name and region in the first line of the config file, e.g. `MyVault|us-west-1`."
	sys.exit(1)

if not len(dirs):
	print r"You need to give the full path to a folder to sync in the second line of the config file, e.g. `C:\backups`. You can list multiple folders, e.g. `C:\backups|D:\backups`"
	sys.exit(1)

for dir in dirs:
	if not os.path.isdir(dir):
		print "Sync directory not found: " + dir
		sys.exit(1)

# Cool! Let's set up everything.
connect_to_region(vault_info[1], aws_access_key_id=access_key_id, aws_secret_access_key=secret_key)
glacier = Layer2(aws_access_key_id=access_key_id, aws_secret_access_key=secret_key, region_name=region)

if arg.backup or arg.delete:
	vault = glacier.get_vault(vault_name)
else:
	print "Creating vault " + vault_name
	vault = glacier.create_vault(vault_name)

# Ah, we don't have a vault listing yet. 
if not ls_present and not arg.create:
	# No job yet? Initiate a job.
	if not inventory_job:
		inventory_job = vault.retrieve_inventory()
		write_config_file()
		print "Requested an inventory. This usually takes about four hours."
		sys.exit(0)
	
	# We have a job, but it's not finished.
	job = vault.get_job(inventory_job)
	if not job.completed:
		print "Waiting for an inventory. This usually takes about four hours."
		sys.exit(0)
	
	# Finished!
	try:
		inventory = json.loads(job.get_output().read())
	except ValueError:
		print "Something went wrong interpreting the data Amazon sent!"
		sys.exit(1)
	
	ls = {}
	for archive in inventory['ArchiveList']:
		ls[archive['ArchiveDescription']] = {
			'id': archive['ArchiveId'],
			'size': int(archive['Size']),
			'hash': archive['SHA256TreeHash']
		}
		
	ls_present = '-'
	inventory_job = ''
	write_config_file()
	print "Imported a new inventory from Amazon."

# Let's upload!
os.stat_float_times(False)
if arg.backup or arg.create:
	try:
		i = 0
		transferred = 0
		time_begin = time.time()
		archives = []
		# Format zip archive from folders
		for dir in dirs:
			name = generate_archive_name(dir)
			print "Creating " + name
			archives.append(name)
			# Import zlib to provide compressing
			import zlib
			zipf = zipfile.ZipFile(name, 'w', zipfile.ZIP_DEFLATED)
			zipdir(dir, zipf)
			zipf.close()

		print "\nBeginning job on " + vault.arn
		for archive in archives:				
			try:
				print archive + ": uploading... ",
				path = os.getcwd() + os.sep + archive
				size = os.path.getsize(path)
				# Fix of bug in boto library. Converts vault name to Unicode
				vault.name = str(vault.name)

				id = vault.concurrent_create_archive_from_file(path, archive)
				ls[archive] = {
					'id': id,
					'size': size
				}
				
				write_config_file()
				i += 1
				transferred += size
				print "done."
			except UploadArchiveError as e:
				print "FAILED TO UPLOAD: " + e.args[0]
			except OSError as e:
				print e.__doc__ + ':' + e.args
			except Exception as e:
				print e.args
			finally:
				# Delete temporary .zip archive
				os.remove(os.getcwd() + os.sep + archive)

				
	finally:
		elapsed_time = time.time() - time_begin
		print "\n" + str(i) + " files successfully uploaded."
		print "Transferred " + format_bytes(transferred) + " in " + format_time(elapsed_time) + " at rate of " + format_bytes(transferred / elapsed_time) + "/s."
		sys.exit(0)

elif arg.delete:
	for name, data in ls.iteritems():
		print 'Remove archive ID : ' + data['id']
		try:
			vault.delete_archive(data['id'])
			print '  Successfully removed archive ' + name
		except Exception as e:
			print e.args

			print 'Sleep 60 sec before retrying...'
			time.sleep(60)

			print 'Retry to remove archive ID : %s' % data['id']
			try:
				vault.delete_archive(data['id'])
				print 'Successfully removed archive ID : %s' % data['id']
			except:
				print 'Cannot remove archive ID : %s' % data['id']

	print 'Removing vault...'
	try:
		vault.delete()
		print 'Vault removed.'
	except Exception as e:
		print "We can't remove the vault now. Please wait some time and try again. You can also remove it from the AWS console, now that all archives have been removed."
		print e.args