import os
import sys
import boto3
import pymysql
import xmltodict
import json
import logging
import xml.etree.ElementTree as ET
from urllib.parse import unquote_plus

file_dir = '/tmp/file.xml'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
ssm = boto3.client('ssm')

def connect_to_database():
    rds_host = os.getenv('RDS_HOST')
    db_name = 'fdbt'
    username = ssm.get_parameter(
        Name='fdbt-rds-reference-data-username',
        WithDecryption=True
    )
    password = ssm.get_parameter(
        Name='fdbt-rds-reference-data-password',
        WithDecryption=True
    )
    try:
        connection = pymysql.connect(
            rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        return connection
    except pymysql.MySQLError as e:
        logger.error(
            "ERROR: Unexpected error: Could not connect to MySQL instance.")
        logger.error(e)
        sys.exit()

    logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']
                       ['object']['key'], encoding='utf-8')
    xmltodict_namespaces = {'http://www.transxchange.org.uk/': None}

    try:
        s3.download_file(bucket, key, file_dir)
        tree = ET.parse(file_dir)
        xml_data = tree.getroot()
        xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
        data_dict = xmltodict.parse(
            xml_string, process_namespaces=True, namespaces=xmltodict_namespaces)
        print(json.dumps(data_dict, indent=4))

        # DATA PROCESSING FUNCTIONS HERE

        insert_into_database(key, bucket)

    except Exception as e:
        print(e)
        raise e


def insert_into_database(key, bucket):
    query_array = [None]
    table_name = ''
    item_count = 0

    connection = connect_to_database()

    for query_line in query_array:
        with connection.cursor() as cursor:
            cursor.execute(query_line)
            connection.commit()
            cursor.execute(f"select * from {table_name}")
            for row in cursor:
                item_count += 1
                logger.info(row)
                print(row)

    connection.commit()
    logger.info("SUCCESS: Data insertion to RDS MySQL instance succeeded")
    return "Added %d items from RDS MySQL table" %(item_count)