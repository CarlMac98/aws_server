# aws_server
A simple python server to demo a couple of aws services

To use it you'll need to 
* create four buckets in S3 and add their names in brackets in *settings_s3buckets.py*; reaname this file *settings.py*
* load the package.zip to a newly created AWS Lambda function. Note that you must select the 3.6 version of Python and configure a trigger to the bucket assigned to TRIGGER in *settings.py*
* click *deploy* on [this site](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:145266761615:applications~ffmpeg-lambda-layer), and again *deploy* in your Lambda's console
* Then you can use the aws_server.py locally or host it on a EC2 instance and access the code via ssh.
