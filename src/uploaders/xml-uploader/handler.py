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

    query = 'INSERT INTO tndsOperatorService (nocCode, lineName, startDate, operatorShortName, serviceDescription) VALUES (%s, %s, %s, %s, %s)', (
        noc_code, line_name, start_date, operator_short_name, service_description)

    try:
        cursor.execute(query)
        operator_service_id = cursor.lastrowid
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsOperatorService table")
        logger.error(e)
        raise e

    logger.info("SUCCESS! Data successfully inserted into tndsOperatorService table")
    return operator_service_id


def collect_journey_pattern_section_refs(raw_journey_patterns):
    journey_pattern_section_refs = []
    for raw_journey_pattern in raw_journey_patterns:
        raw_journey_pattern_section_refs = raw_journey_pattern['JourneyPatternSectionRefs']
        journey_pattern_section_refs.append(raw_journey_pattern_section_refs)
    return journey_pattern_section_refs


def collect_journey_patterns(data_dict):
    raw_journey_patterns = data_dict['TransXChange']['Services']['Service']['StandardService']['JourneyPattern']
    raw_journey_pattern_sections = data_dict['TransXChange']['JourneyPatternSections']['JourneyPatternSection']

    journey_pattern_section_refs = collect_journey_pattern_section_refs(raw_journey_patterns)

    journey_patterns = []
    for journey_pattern in journey_pattern_section_refs:
        journey_pattern_sections = []
        for journey_pattern_section_ref in journey_pattern:
            for raw_journey_pattern_section in raw_journey_pattern_sections:
                selected_raw_journey_pattern_section = []
                if raw_journey_pattern_section['@id'] == journey_pattern_section_ref:
                    selected_raw_journey_pattern_section = raw_journey_pattern_section
                if len(selected_raw_journey_pattern_section) > 0:
                    raw_journey_pattern_timing_links = selected_raw_journey_pattern_section['JourneyPatternTimingLink']
                    journey_pattern_timing_links = []
                    for raw_journey_pattern_timing_link in raw_journey_pattern_timing_links:
                        journey_pattern_timing_link = {}
                        journey_pattern_timing_link['from_atco_code'] = raw_journey_pattern_timing_link['From']['StopPointRef']
                        journey_pattern_timing_link['from_timing_status'] = raw_journey_pattern_timing_link['From']['TimingStatus']
                        journey_pattern_timing_link['to_atco_code'] = raw_journey_pattern_timing_link['To']['StopPointRef']
                        journey_pattern_timing_link['to_timing_status'] = raw_journey_pattern_timing_link['To']['TimingStatus']
                        journey_pattern_timing_link['run_time'] = raw_journey_pattern_timing_link['RunTime']
                        # journey_pattern_timing_link['order'] = raw_journey_pattern_timing_link[order]
                        journey_pattern_timing_links.append(journey_pattern_timing_link)
                    journey_pattern_sections.append(journey_pattern_timing_links)
        journey_patterns.append(journey_pattern_sections)
    return journey_patterns


def iterate_through_journey_patterns_and_run_insert_queries(cursor, data_dict, operator_service_id):
    journey_patterns = collect_journey_patterns(data_dict)
    for journey_pattern in journey_patterns:
        for journey_pattern_section in journey_pattern:
            journey_pattern_section_id = insert_into_tnds_journey_pattern_section_table(cursor, operator_service_id)
            for journey_pattern_timing_link in journey_pattern_section:
                insert_into_tnds_journey_pattern_link_table(cursor, journey_pattern_timing_link, journey_pattern_section_id)


def insert_into_tnds_journey_pattern_section_table(cursor, operator_service_id):
    query = 'INSERT INTO tndsJourneyPatternSection (operatorServiceId) VALUES (%s)', (
        operator_service_id)

    try:
        cursor.execute(query)
        journey_pattern_section_id = cursor.lastrowid
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsJourneyPatternSection table")
        logger.error(e)
        raise e

    logger.info("SUCCESS! Data successfully inserted into tndsJourneyPatternSection table")
    return journey_pattern_section_id


def insert_into_tnds_journey_pattern_link_table(cursor, journey_pattern_timing_link, journey_pattern_section_id):
    from_atco_code = journey_pattern_timing_link['From']['StopPointRef']
    from_timing_status = journey_pattern_timing_link['From']['TimingStatus']
    to_atco_code = journey_pattern_timing_link['To']['StopPointRef']
    to_timing_status = journey_pattern_timing_link['To']['TimingStatus']
    run_time = journey_pattern_timing_link['RunTime']

    # WHAT IS ORDER??
    order = ''

    query = 'INSERT INTO tndsJourneyPatternLink (journeyPatternSectionId, fromAtcoCode, fromTimingStatus, toAtcoCode, toTimingStatus, runtime, order) VALUES (%s, %s, )', (
        journey_pattern_section_id, from_atco_code, from_timing_status, to_atco_code, to_timing_status, run_time, order)

    try:
        cursor.execute(query)
    except Exception as e:
        logger.error(
            "ERROR! Unexpected error. Could not execute query on tndsJourneyPatternLink table")
        logger.error(e)
        raise e

    logger.info("SUCCESS! Data successfully inserted into tndsJourneyPatternLink table")
    return


def write_to_database(data_dict):
    connection = connect_to_database()

    try:
        with connection.cursor() as cursor:
            operator_service_id = insert_into_tnds_operator_service_table(
                cursor, data_dict)
            iterate_through_journey_patterns_and_run_insert_queries(cursor, data_dict, operator_service_id)
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
        logger.error(e)
        raise e
