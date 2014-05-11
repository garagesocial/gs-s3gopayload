#!/usr/bin/python

###############################################################################
### Garagesocial, Inc. - https://www.garagesocial.com
###############################################################################
###
### Filename:  gs_s3gopayload.py
###
### About:     Python script to deploy a set of files and directories as a hash
###            named zip to Amazon S3. Useful for integration with Beanstalk
###            type systems allowing to keep the git repo free of non essential
###            clutter such as the vendor directory with composer yet provide a
###            venue for re-integration.
###
### Usage:
###            s3gp = gs_s3gopayload(
###                     'bucket name', 'accesskeyid',
###                     'secretkey', '/home/gs/srp3j',
###                     ['someProjectFolder/vendo', 'someProjectFolder/config']
###
###            s3gp.start()
###
### Dependencies:
###            easy_install GitPython
###            easy_install boto
###
### Documentation Reference: https://docs.python.org/devguide/documenting.html
###
###############################################################################
###
### The MIT License (MIT)
###
### Copyright (c) 2014 Garagesocial, Inc.
###
### Permission is hereby granted, free of charge, to any person obtaining a
### copy of this software and associated documentation files (the "Software"),
### to deal in the Software without restriction, including without limitation
### the rights to use, copy, modify, merge, publish, distribute, sublicense,
### and/or sell copies of the Software, and to permit persons to whom the
### Software is furnished to do so, subject to the following conditions:
###
### The above copyright notice and this permission notice shall be included in
### all copies or substantial portions of the Software.
###
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
### IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
### THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
### FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
### DEALINGS IN THE SOFTWARE.
###
###############################################################################

import os, shutil, zipfile, stat, sys
from git import *
from boto.s3.connection import S3Connection

class gs_s3gopayload:
   # s3 bucket name
   s3_bucket = ''
   # s3 access key
   s3_access_id = ''
   # s3 secret key
   s3_secret_key = ''
   # abs path to git root
   git_root_abs_path = ''
   # relative path (to git_root_abs_path) to directories and files
   rel_paths_to_zip = []
   # name of temp directory to create
   tmp_root_dir = '_gs_s3gopayload'

   def __init__(self, s3_bucket, s3_access_id, s3_secret_key, git_root_abs_path, rel_paths_to_zip):
      self.s3_bucket = s3_bucket
      self.s3_access_id = s3_access_id
      self.s3_secret_key = s3_secret_key
      self.git_root_abs_path = git_root_abs_path
      self.rel_paths_to_zip = rel_paths_to_zip

   def start(self):
      # instantiate the git object
      repo = Repo(self.git_root_abs_path, odbt=GitCmdObjectDB)
      # get head git commit sha (to be used as the zip file name)
      head_git_sha = str(repo.head.commit.hexsha)
      # get current branch name
      head_git_branch = str(repo.head.reference)
      # combine both values
      head_git_branch_sha = head_git_branch  + '/' + head_git_sha

      # specify name and location of temp directory to work in (helps for cleanup purposes)
      tmp_dir = os.path.join(self.git_root_abs_path, self.tmp_root_dir, head_git_branch_sha)

      # if already exists delete it and recreate it
      if os.path.exists(tmp_dir): self.del_dir_recursive(tmp_dir)
      # create the temp direc
      os.makedirs(tmp_dir)

      # destination of output zip file
      zip_output_path = tmp_dir + '/' + head_git_sha + '.zip'

      # iterate through paths specified to include in zip
      for relPath in self.rel_paths_to_zip:
         abs_path = os.path.abspath(relPath)
         print 'Processing... ' + abs_path
         if os.path.exists(abs_path): self.zip_dir(self.git_root_abs_path, abs_path, zip_output_path)

      # upload zip to s3
      self.zip_upload_s3(self.s3_bucket, self.s3_access_id, self.s3_secret_key, head_git_branch_sha + '.zip', zip_output_path)
      self.zip_upload_s3(self.s3_bucket, self.s3_access_id, self.s3_secret_key, 'latest.zip', zip_output_path)
      # cleanup temp directory
      self.del_dir_recursive(tmp_dir)

   # Upload the set of key/filepath to s3
   #
   # @param  string s3_bucket      (ex: mybucket)
   # @param  string s3_access_id   (ex: H0QGLR8VRK55N07KW35R)
   # @param  string s3_secret_key  (ex: K7sFcLas5LohfAURXH1MlJLDoRdSCQq8EdXVQxPN)
   # @param  string s3Key          (ex: 41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
   # @param  string s3KeySource    (ex: myfolder/41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
   # @return void
   def zip_upload_s3(self, s3_bucket, s3_access_id, s3_secret_key, s3Key, s3KeySource):
      connection_instance = S3Connection(s3_access_id, s3_secret_key)
      bucket_instance = connection_instance.get_bucket(s3_bucket)

      # if source file does not exist return
      if not os.path.isfile(s3KeySource) : return
      # if key exists delete it
      if bucket_instance.get_key(s3Key) : bucket_instance.delete_key(s3Key)

      # upload file using sha as name
      if bucket_instance.get_key(s3Key) : bucket_instance.delete_key(s3Key)
      s3_key_new = bucket_instance.new_key(s3Key)
      s3_key_new.set_contents_from_filename(s3KeySource)
      # s3_key_new.set_acl('public-read')

   # Zip the specified path into the specified zip. If zip already exists it will append.
   #
   # @param    string rel_to_dir      (ex: /home/gs/s3prj) This is essentially the git_root_abs_path
   # @param    string source_dir      (ex: /home/gs/s3prj/gs) The rel_to_dir will be eaten out of this path
   # @param    string zip_output_path (ex: /home/gs/s3prj/tmp/41bd49f08f5daad48edd9b2202decg2ac405bfa5/41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
   # @return   void
   def zip_dir(self, rel_to_dir, source_dir, zip_output_path):
      # if zip file already exists then append to it otherwise write a new one
      zip_mode = "a" if os.path.isfile(zip_output_path) else "w"
      with zipfile.ZipFile(zip_output_path, zip_mode, zipfile.ZIP_DEFLATED) as zip:
         for root, dirs, files in os.walk(source_dir):
            # add empty directories
            zip.write(root, os.path.relpath(root, rel_to_dir))
            for file in files:
               filename = os.path.join(root, file)
               # regular files only
               if os.path.isfile(filename):
                  zip_specific_path = os.path.join(os.path.relpath(root, rel_to_dir), file)
                  zip.write(filename, zip_specific_path)

   # Recursively delete the target_dir and handle the permission problems that could arise in windows
   # Credits: Epcylon @ SO
   #
   # @param    string  target_dir   (ex: /home/gs/s3prj/tmp/41bd49f08f5daad48edd9b2202decg2ac405bfa5)
   # @return   void
   def del_dir_recursive(self, target_dir):
      for root, dirs, files in os.walk(target_dir, topdown=False):
         for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
         for name in dirs:
            os.rmdir(os.path.join(root, name))
      shutil.rmtree(target_dir)

# End of gs_s3gopayload.py

