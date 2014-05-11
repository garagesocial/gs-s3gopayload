gs_s3gopayload
===============


This script takes for input an **array of paths** to local **files** and **directories** in your git project. From there the script will clone the structure and files into a zip file (named after the git sha of the HEAD). Finally the script will upload this zip file to S3 for retrieval on the deployed systems and extraction.

## Overview
![diagram](https://github.com/garagesocial/gs-s3gopayload/blob/master/doc/diagram.PNG?raw=true)

## Requirements
* `easy_install GitPython`
* `easy_install boto`

## Advantages
Keep your git repo fast and clutter free from things such as the 'vendor' directory when using composer. This vendor folder is required to run your application but can contains hundreds of thousands of files written by third parties. This script allows to package it all up and make it readily available online for download and extraction on your live instances.

## Requirements

  * GitPython Driver
    * `easy_install GitPython`
    * `easy_install boto`

## Usage
* [Instantiate and Run](#instantiate-run)
* [Server Download](#server-download)
* [Server Download Specific](#server-download-specific)


<a name="instantiate-run"></a>
## Instantiate and Run

```python
import s3gopayload
s3gp = s3gopayload.s3gopayload('bucket name', 'accesskeyid', 'secretkey', '/home/gs/srp3j', ['someProjectFolder/vendo', 'someProjectFolder/config' ]
s3gp.start()
```

gs_s3gopayload is licensed under the terms of the [MIT License](http://opensource.org/licenses/MIT)

<a name="server-download"></a>
## Server Download
Finally on your beanstalk config set for download and extraction
```python
container_commands:
   "00-fetch-flash-clone":
      command: "cd /var/app/ondeck; wget https://s3.amazonaws.com/my-s3/latest.zip; unzip latest.zip; rm latest.zip"
```


<a name="server-download-specific"></a>
## Server Download Specific
To make use of the rollback feature in beanstalk, we need to keep a specific copy of the specific file. Since latest.zip gets overwritten after every push we can't rely on this. This below method allows for the precise retrieval of the correct zip and allows for rollbacks.
```python
container_commands:
   "00-fetch-flash-clone":
      command: "cd /var/app/ondeck; export git_sha=$(cat /var/log/eb-version-deployment.log | grep -oP 'git-\\K[A-Fa-f\\d]+' | tail -1); wget https://s3.amazonaws.com/my-s3/master/$git_sha.zip; unzip -o $git_sha.zip; rm $git_sha.zip"
```

### License
gs_s3gopayload is licensed under the terms of the [MIT License](http://opensource.org/licenses/MIT)

