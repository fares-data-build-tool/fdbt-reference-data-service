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
    print(rds_host)
    db_name = 'fdbt'
    print(db_name)
    username = ssm.get_parameter(
        Name='fdbt-rds-reference-data-username',
        WithDecryption=True
    )['Parameter']['Value']
    print(username)
    password = ssm.get_parameter(
        Name='fdbt-rds-reference-data-password',
        WithDecryption=True
    )['Parameter']['Value']
    print(password)
    try:
        connection = pymysql.connect(
            rds_host, user=username, passwd=password, db=db_name, connect_timeout=5)
        return connection
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not connect to MySQL instance")
        logger.error(e)
        sys.exit()
        raise e

    logger.info("SUCCESS! Connection to RDS MySQL instance succeeded")


def insert_into_tnds_operator_service_table(cursor, data_dict):
    operators = data_dict['TransXChange']['Operators']['Operator']
    services = data_dict['TransXChange']['Services']['Service']
    noc_code = operators['NationalOperatorCode']
    line_name = services['Lines']['Line']['LineName']
    start_date = services['OperatingPeriod']['StartDate']
    operator_short_name = operators['OperatorShortName']
    service_description = services['Description']

    query = "INSERT INTO tndsOperatorService (nocCode, lineName, startDate, operatorShortName, serviceDescription) VALUES (%s, %s, %s, %s, %s)"

    try:
        print("Writing to tndsOperatorService table...")
        cursor.execute(query, (noc_code, line_name, start_date,
                               operator_short_name, service_description))
        operator_service_id = cursor.lastrowid
        print("Write complete! Id is: ", operator_service_id)
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsOperatorService table")
        logger.error(e)
        raise e

    logger.info(
        "SUCCESS! Data successfully inserted into tndsOperatorService table")
    return operator_service_id


def collect_journey_pattern_section_refs(raw_journey_patterns):
    journey_pattern_section_refs = []
    for raw_journey_pattern in raw_journey_patterns:
        raw_journey_pattern_section_refs = raw_journey_pattern['JourneyPatternSectionRefs']
        journey_pattern_section_refs.append(raw_journey_pattern_section_refs)
    print("journey_pattern_section_refs", journey_pattern_section_refs)
    return journey_pattern_section_refs


def collect_journey_patterns(data_dict):
    raw_journey_patterns = data_dict['TransXChange']['Services']['Service']['StandardService']['JourneyPattern']
    raw_journey_pattern_sections = data_dict['TransXChange'][
        'JourneyPatternSections']['JourneyPatternSection']

    journey_pattern_section_refs = collect_journey_pattern_section_refs(
        raw_journey_patterns)

    journey_patterns = []
    for journey_pattern in journey_pattern_section_refs:
        journey_pattern_sections = []
        for journey_pattern_section_ref in journey_pattern:
            for raw_journey_pattern_section in raw_journey_pattern_sections:
                selected_raw_journey_pattern_section = []
                if raw_journey_pattern_section['@id'] == journey_pattern_section_ref:
                    selected_raw_journey_pattern_section = raw_journey_pattern_section
                if len(selected_raw_journey_pattern_section) > 0:
                    raw_journey_pattern_timing_links = selected_raw_journey_pattern_section[
                        'JourneyPatternTimingLink']
                    if not isinstance(raw_journey_pattern_timing_links, list):
                        raw_journey_pattern_timing_links = [
                            raw_journey_pattern_timing_links]
                    journey_pattern_timing_links = []
                    for raw_journey_pattern_timing_link in raw_journey_pattern_timing_links:
                        journey_pattern_timing_link = {}
                        journey_pattern_timing_link['from_atco_code'] = raw_journey_pattern_timing_link['From']['StopPointRef']
                        journey_pattern_timing_link['from_timing_status'] = raw_journey_pattern_timing_link['From']['TimingStatus']
                        journey_pattern_timing_link['to_atco_code'] = raw_journey_pattern_timing_link['To']['StopPointRef']
                        journey_pattern_timing_link['to_timing_status'] = raw_journey_pattern_timing_link['To']['TimingStatus']
                        journey_pattern_timing_link['run_time'] = raw_journey_pattern_timing_link['RunTime']
                        # journey_pattern_timing_link['order'] = raw_journey_pattern_timing_link[order]
                        journey_pattern_timing_links.append(
                            journey_pattern_timing_link)
                    journey_pattern_sections.append(
                        journey_pattern_timing_links)
        journey_patterns.append(journey_pattern_sections)
    return journey_patterns


def iterate_through_journey_patterns_and_run_insert_queries(cursor, data_dict, operator_service_id):
    journey_patterns = collect_journey_patterns(data_dict)
    for journey_pattern in journey_patterns:
        for journey_pattern_section in journey_pattern:
            journey_pattern_section_id = insert_into_tnds_journey_pattern_section_table(
                cursor, operator_service_id)
            print(journey_pattern_section)
            count = 1
            for journey_pattern_timing_link in journey_pattern_section:
                insert_into_tnds_journey_pattern_link_table(
                    cursor, journey_pattern_timing_link, journey_pattern_section_id, count)
                count +=1


def insert_into_tnds_journey_pattern_section_table(cursor, operator_service_id):
    query = "INSERT INTO tndsJourneyPatternSection (operatorServiceId) VALUES (%s)"

    try:
        print("Writing to tndsJourneyPatternSection table...")
        cursor.execute(query, (operator_service_id))
        journey_pattern_section_id = cursor.lastrowid
        print("Write complete! Id is: ", journey_pattern_section_id)
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsJourneyPatternSection table")
        logger.error(e)
        raise e

    logger.info(
        "SUCCESS! Data successfully inserted into tndsJourneyPatternSection table")
    return journey_pattern_section_id


def insert_into_tnds_journey_pattern_link_table(cursor, journey_pattern_timing_link, journey_pattern_section_id, count):
    print(journey_pattern_timing_link)
    from_atco_code = journey_pattern_timing_link['from_atco_code']
    from_timing_status = journey_pattern_timing_link['from_timing_status']
    to_atco_code = journey_pattern_timing_link['to_atco_code']
    to_timing_status = journey_pattern_timing_link['to_timing_status']
    run_time = journey_pattern_timing_link['run_time']
    order_in_sequence = count

    query = "INSERT INTO tndsJourneyPatternLink (journeyPatternSectionId, fromAtcoCode, fromTimingStatus, toAtcoCode, toTimingStatus, runtime, orderInSequence) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    try:
        print("Writing to tndsJourneyPatternLink table...")
        cursor.execute(query, (journey_pattern_section_id, from_atco_code,
                               from_timing_status, to_atco_code, to_timing_status, run_time, order_in_sequence))
        logger.info(
            "SUCCESS! Data successfully inserted into tndsJourneyPatternLink table")
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsJourneyPatternLink table")
        logger.error(e)
        raise e


def write_to_database(data_dict):
    try:
        connection = connect_to_database()
        with connection.cursor() as cursor:
            operator_service_id = insert_into_tnds_operator_service_table(
                cursor, data_dict)
            iterate_through_journey_patterns_and_run_insert_queries(
                cursor, data_dict, operator_service_id)
            connection.commit()

    except Exception as e:
        connection.rollback()
        logger.error("ERROR! Unexpected error. Could not write to database")
        logger.error(e)
        raise e

    finally:
        connection.close()


def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']
                       ['object']['key'], encoding='utf-8')

    print('Bucket is: ', bucket)
    print('Key is: ', key)

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

        logger.info("Starting write to database...")
        write_to_database(data_dict)
        logger.info(
            "SUCCESS! Succesfully wrote contents of '{}' from '{}' bucket to database.".format(key, bucket))

    except Exception as e:
        logger.error(e)
        raise e
