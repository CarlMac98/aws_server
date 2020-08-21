# aws_server
A simple python server to demo a couple of aws services

To use it you'll need to 
1. [create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) with a key pair
2. Download the [AWS CLI](https://aws.amazon.com/cli/?nc1=h_ls) and type on a terminal "*aws configure*"; then insert the public and the private key, the region and type "text" for the last option
3. create four buckets in S3 and add their names in brackets in *settings_s3buckets.py*; reaname this file *settings.py*
4. load the package.zip to a newly created AWS Lambda function. Note that you must select the 3.6 version of Python and configure a trigger to the bucket assigned to TRIGGER in *settings.py*
5. click *deploy* on [this site](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:145266761615:applications~ffmpeg-lambda-layer), and again *deploy* in your Lambda's console
6. Then you can use the aws_server.py locally or host it on a EC2 instance and access the code via ssh. In the second case, the point "2." needs to be done on the remote machine
