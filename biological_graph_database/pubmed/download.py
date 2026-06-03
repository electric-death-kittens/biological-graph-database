

#
# load useful libraries
#
import requests
import os
import json
import hashlib
from ftplib import FTP

#
# user settings
#
ftp_pubmed_root = 'ftp.ncbi.nlm.nih.gov'
remote_directory = '/pubmed/baseline'
email_address = 'emw314159@gmail.com'
directory_download_to = os.environ['HOME'] + '/Downloads/pubmed'
filename_failed_downloads = 'failed_download_filenames.json'

#
# get a list of the files to download
#
pubmed_xml_list = []
with FTP(ftp_pubmed_root) as ftp:
    ftp.login(user="anonymous", passwd = email_address)
    ftp.cwd(remote_directory)    
    pubmed_xml_list = sorted([x.strip() for x in ftp.nlst() if not x.strip() == ''])
    pubmed_xml_list = [x for x in pubmed_xml_list if '.'.join(x.split('.')[-2:]) == 'xml.gz']

#
# QA #1
#
assert len(pubmed_xml_list) > 0

#
# Define a function for downloading a file
#
def download_file(url, folder):
    os.makedirs(folder, exist_ok=True) # Ensure directory exists
    filename = url.split("/")[-1]
    path = os.path.join(folder, filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return path

#
# define a function for computing MD5 for a file
#
def compute_file_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        # Read the file in small chunks
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

#
# define a function for reading an MD5 file
#
def read_md5_file(md5_file_path):
    with open(md5_file_path, "r") as f:
        # Get the first word (the hash) and strip any whitespace
        return f.read().split('=')[-1].strip().lower()

#
# download and MD5-check XML files
#
list_filenames_failed = []
for filename in pubmed_xml_list:
    try:
        file_to_process = download_file('http://' + ftp_pubmed_root + '/' + remote_directory + '/' + filename, directory_download_to)
        file_to_process_md5 = download_file('http://' + ftp_pubmed_root + '/' + remote_directory + '/' + filename + '.md5', directory_download_to)
        assert compute_file_md5(file_to_process) == read_md5_file(file_to_process_md5)
    except:
        list_filenames_failed.append(filename)

#
# save the list of filenames that failed
#
with open(filename_failed_downloads, 'w') as f:
    f.write(json.dumps({'failed_downloads' : list_filenames_failed}, indent = 4) + '\n')
