#!/usr/bin/python
# Filename: s3gopayload.py
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Garagesocial, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Genesys - 2013/12/04 - Maxime Rassi <maxime@garagesocial.com>

import os, shutil, zipfile, stat, sys
from git import *
from boto.s3.connection import S3Connection

class s3gopayload:
  # s3 bucket name
  s3Bucket = ''
  # s3 access key
  s3AccessKeyId = ''
  # s3 secret key
  s3SecretKey = ''
  # abs path to git root
  gitRootAbsPath = ''
  # relative path (to gitRootAbsPath) to directories and files
  relPathsToZip = []
  # name of temp directory to create
  tmpRootDir = '_s3gopayload'

  def __init__(self, s3Bucket, s3AccessKeyId, s3SecretKey, gitRootAbsPath, relPathsToZip):
    self.s3Bucket = s3Bucket
    self.s3AccessKeyId = s3AccessKeyId
    self.s3SecretKey = s3SecretKey
    self.gitRootAbsPath = gitRootAbsPath
    self.relPathsToZip = relPathsToZip

  def start(self):
    # instantiate the git object
    repo = Repo(self.gitRootAbsPath, odbt=GitCmdObjectDB)
    # get head git commit sha (to be used as the zip file name)
    headGitSha = str(repo.head.commit.hexsha)
    # get current branch name
    headGitBranch = str(repo.head.reference)
    # combine both values
    headGitBranchSha = headGitBranch  + '/' + headGitSha

    # specify name and location of temp directory to work in (helps for cleanup purposes)
    tmpDir = os.path.join(self.gitRootAbsPath, self.tmpRootDir, headGitBranchSha)

    # if already exists delete it and recreate it
    if os.path.exists(tmpDir): self.delDirRecursive(tmpDir)
    # create the temp direc
    os.makedirs(tmpDir)

    # destination of output zip file
    zipOutputPath = tmpDir + '/' + headGitSha + '.zip'

    # iterate through paths specified to include in zip
    for relPath in self.relPathsToZip:
      absPath = os.path.abspath(relPath)
      print 'Processing... ' + absPath
      if os.path.exists(absPath): self.zipDir(self.gitRootAbsPath, absPath, zipOutputPath)

    # upload zip to s3
    self.zipUploadS3(self.s3Bucket, self.s3AccessKeyId, self.s3SecretKey, headGitBranchSha + '.zip', zipOutputPath)
    self.zipUploadS3(self.s3Bucket, self.s3AccessKeyId, self.s3SecretKey, 'latest.zip', zipOutputPath)
    # cleanup temp directory
    self.delDirRecursive(tmpDir)

  # Upload the set of key/filepath to s3
  #
  # s3Bucket      (i.e.: mybucket)
  # s3AccessKeyId (i.e.: H0QGLR8VRK55N07KW35R)
  # s3SecretKey   (i.e.: K7sFcLas5LohfAURXH1MlJLDoRdSCQq8EdXVQxPN)
  # s3Key         (i.e.: 41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
  # s3KeySource   (i.e.: myfolder/41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
  def zipUploadS3(self, s3Bucket, s3AccessKeyId, s3SecretKey, s3Key, s3KeySource):
    connectionInstance = S3Connection(s3AccessKeyId, s3SecretKey)
    bucketInstance = connectionInstance.get_bucket(s3Bucket)

    # if source file does not exist return
    if not os.path.isfile(s3KeySource) : return
    # if key exists delete it
    if bucketInstance.get_key(s3Key) : bucketInstance.delete_key(s3Key)

    # upload file using sha as name
    if bucketInstance.get_key(s3Key) : bucketInstance.delete_key(s3Key)
    s3KeyNew = bucketInstance.new_key(s3Key)
    s3KeyNew.set_contents_from_filename(s3KeySource)
    # s3KeyNew.set_acl('public-read')


  # Zip the specified path into the specified zip. If zip already exists it will append.
  #
  # relToDir      (i.e.: /home/gs/s3prj) This is essentially the gitRootAbsPath
  # sourceDir     (i.e.: /home/gs/s3prj/gs) The relToDir will be eaten out of this path
  # zipOutputPath (i.e.: /home/gs/s3prj/tmp/41bd49f08f5daad48edd9b2202decg2ac405bfa5/41bd49f08f5daad48edd9b2202decg2ac405bfa5.zip)
  def zipDir(self, relToDir, sourceDir, zipOutputPath):
    # if zip file already exists then append to it otherwise write a new one
    zipMode = "a" if os.path.isfile(zipOutputPath) else "w"
    with zipfile.ZipFile(zipOutputPath, zipMode, zipfile.ZIP_DEFLATED) as zip:
      for root, dirs, files in os.walk(sourceDir):
        # add empty directories
        zip.write(root, os.path.relpath(root, relToDir))
        for file in files:
          filename = os.path.join(root, file)
          # regular files only
          if os.path.isfile(filename):
            zipSpecificPath = os.path.join(os.path.relpath(root, relToDir), file)
            zip.write(filename, zipSpecificPath)

  # Recursively delete the targetDir and handle the permission problems that could arise in windows
  # Credits: Epcylon @ SO
  #
  # targetDir (i.e.: /home/gs/s3prj/tmp/41bd49f08f5daad48edd9b2202decg2ac405bfa5)
  def delDirRecursive(self, targetDir):
    for root, dirs, files in os.walk(targetDir, topdown=False):
      for name in files:
        filename = os.path.join(root, name)
        os.chmod(filename, stat.S_IWUSR)
        os.remove(filename)
      for name in dirs:
        os.rmdir(os.path.join(root, name))
    shutil.rmtree(targetDir)

# End of s3gopayload.py

