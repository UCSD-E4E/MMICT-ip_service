import configparser
import os.path

import boto3

image_folder = 'images'
config_file = 'service/S3Access.ini'
config_section = 'AWS_S3'
download_img = 'output.tif'


def getImg(img_ref):
    """
    input: image reference to S3
    output: image data
    """
    downloadImg(img_ref)

    return "img"


def downloadImg(img_ref):
    config = configparser.ConfigParser()
    config.read(config_file)
    s3_section = config[config_section]
    access_key = s3_section['aws_access_key_id']
    secret_key = s3_section['aws_secret_access_key']
    bucket_name = s3_section['bucket_name']

    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    s3_client.download_file(bucket_name, img_ref, os.path.join(image_folder, download_img))
