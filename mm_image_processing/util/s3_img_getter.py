import configparser
import os
import logging
import boto3

from dotenv import load_dotenv

load_dotenv()
# Load S3 credentials from .env (defined in Docker compose)
bucket_name = os.getenv("AWS_BUCKET_NAME")

# For no folder in S3 bucket, use the following
image_folder = ''

# config_file = 'util/s3_access.cfg'
# config_section = 'AWS_S3'

def getImg(img_ref, app):
    """
    input: image reference to S3
    output: image url
    """
    
    imgUrl = os.path.join(image_folder, img_ref)
    # config = configparser.ConfigParser()
    # config.read(config_file)
    # s3_section = config[config_section]
    # access_key = s3_section['aws_access_key_id']
    # secret_key = s3_section['aws_secret_access_key']
    # bucket_name = s3_section['bucket_name']

    s3_client = boto3.client('s3')
    
    s3_client.download_file(bucket_name, img_ref, imgUrl)

    return imgUrl

def deleteImg():
    pass
