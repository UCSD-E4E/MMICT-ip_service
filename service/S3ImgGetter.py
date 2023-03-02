import os.path

import boto3

access_key = 'AKIAWFXD2W3W5JSAJIMW'
secret_key = '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'
bucket_name = 'mangrove-monitoring-images'
image_folder = './'


def getImg(img_ref):
    """
    input: image reference to S3
    output: image data
    """
    downloadImg(img_ref)

    return "img"


def downloadImg(img_ref):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    s3_client.download_file(bucket_name, 'example_input_image.tif', os.path.join(image_folder, 'test.tif'))
