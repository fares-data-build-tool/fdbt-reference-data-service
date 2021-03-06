import urllib.parse
import boto3
import os
import logging
from zipfile import ZipFile

file_dir = '/tmp/file.zip'

s3 = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        s3.download_file(bucket, key, file_dir)
        zipfile = ZipFile(file_dir)

        key_base = os.path.splitext(key)[0]

        for filename in zipfile.namelist():
            if filename.endswith('.xml'):
                s3.upload_fileobj(
                    zipfile.open(filename),
                    os.getenv('BUCKET_NAME'),
                    key_base + '/' + os.path.basename(filename),
                    ExtraArgs={
                        'ContentType': 'application/xml'
                    }
                )
    except Exception as e:
        logger.error(e)
        logger.error(
            'Error getting object {} from bucket {}.'.format(key, bucket))
        raise e
