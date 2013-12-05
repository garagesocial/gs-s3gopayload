S3GoPayload
===============

Intro
-------------------------
This script takes for input an **array of paths** to local **files** and **directories** in your git project. From there the script will clone the structure and files into a zip file (named after the git sha of the HEAD). Finally the script will upload this zip file to S3 for retrieval on the deployed systems and extraction.

Visualize
-------------------------
![diagram](https://github.com/garagesocial/gs-s3gopayload/blob/master/doc/diagram.PNG?raw=true)

Advantages
-------------------------
Keep your git repo fast and clutter free from things such as the 'vendor' directory when using composer. This vendor folder is required to run your application but can contains hundreds of thousands of files written by third parties. This script allows to package it all up and make it readily available online for download and extraction on your live instances.

Dependencies
-------------------------
* `easy_install GitPython`
* `easy_install botto`

Usage
-------------------------
```python
import s3gopayload
s3gp = s3gopayload.s3gopayload('bucket name', 'accesskeyid', 'secretkey', '/home/gs/srp3j', ['someProjectFolder/vendo', 'someProjectFolder/config' ]
s3gp.start()
```
