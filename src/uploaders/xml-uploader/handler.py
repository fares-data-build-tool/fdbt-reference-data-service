import os
import sys
import boto3
import pymysql
import xmltodict
import json
import logging
import xml.etree.ElementTree as ET
from urllib.parse import unquote_plus

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


def insert_into_tnds_service_table(connection, data_dict):
    services = data_dict['TransXChange']['Services']['Service']
    noc_code = data_dict['TransXChange']['Operators']['Operator']['NationalOperatorCode']
    line_name = services['Lines']['Line']['LineName']
    start_date = services['OperatingPeriod']['StartDate']

    # Both below are from servicereport.csv
    region_code = ''
    region_operator_code = ''

    service_code = services['ServiceCode']
    description = services['Description']
    query = 'INSERT INTO tndsService (nocCode, lineName, startDate, regionCode, regionOperatorCode, serviceCode, description) VALUES (%s, %s, %s, %s, %s, %s, %s)', (
        noc_code, line_name, start_date, region_code, region_operator_code, service_code, description)

    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()

    logger.info("SUCCESS: Data insertion to RDS MySQL instance succeeded")
    return


def insert_into_tnds_operator_service_table(connection, data_dict):
    operators = data_dict['TransXChange']['Operators']['Operator']
    services = data_dict['TransXChange']['Services']['Service']
    noc_code = operators['NationalOperatorCode']
    line_name = services['Lines']['Line']['LineName']
    start_date = services['OperatingPeriod']['StartDate']
    operator_short_name = operators['OperatorShortName']
    service_description = services['Description']

    query = 'INSERT INTO tndsOperatorService (nocCode, lineName, startDate, operatorShortName, serviceDescription) VALUES (%s, %s, %s, %s, %s)', (
        noc_code, line_name, start_date, operator_short_name, service_description)

    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()

    logger.info("SUCCESS: Data insertion to RDS MySQL instance succeeded")
    return


def insert_into_tnds_journey_pattern_section_table(connection, data_dict):
    # TODO Modify query to be nested/sub query with SELECT and INSERT
    query = 'INSERT INTO tndsJourneyPatternSection (operatorServiceId) VALUES (%s)', ()

    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()

    logger.info("SUCCESS: Data insertion to RDS MySQL instance succeeded")
    return


def insert_into_tnds_journey_pattern_timing_link_table(connection, data_dict):
    # TODO Modify query to be nested/sub query with SELECT and INSERT
    query = 'INSERT INTO tndsJourneyPatternLink (journeyPatternSectionId, fromAtcoCode, fromTimingStatus, toAtcoCode, toTimingStatus, runtime, order) VALUES ()'.format

    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()

    logger.info("SUCCESS: Data insertion to RDS MySQL instance succeeded")
    return


def write_to_database(data_dict):
    connection = connect_to_database()
    # TODO Use transactions
    try:
        insert_into_tnds_service_table(connection, data_dict)
        insert_into_tnds_operator_service_table(connection, data_dict)
        insert_into_tnds_journey_pattern_section_table(connection, data_dict)
        insert_into_tnds_journey_pattern_timing_link_table(
            connection, data_dict)
    except Exception as e:
        logger.error(e)
        raise e
    finally:
        connection.close()


def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']
                       ['object']['key'], encoding='utf-8')
    file_dir = '/tmp/' + key.split('/')[-1]
    xmltodict_namespaces = {'http://www.transxchange.org.uk/': None}
    table_names = ['tndsService', 'tndsOperatorService',
                   'tndsJourneyPatternSection', 'tndsJourneyPatternLink']

    try:
        s3.download_file(bucket, key, file_dir)
        logger.info("Downloaded S3 file, '{}' to '{}'".format(key, file_dir))
        tree = ET.parse(file_dir)
        xml_data = tree.getroot()
        xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
        data_dict = xmltodict.parse(
            xml_string, process_namespaces=True, namespaces=xmltodict_namespaces)

        write_to_database(data_dict)

    except Exception as e:
        print(e)
        raise e
