import os
import sys
import boto3
import pymysql
import xmltodict
from joblib import Parallel, delayed
import multiprocessing
from pathlib import Path
import json
import logging
import xml.etree.ElementTree as ET
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def connect_to_database():
    # rds_host = os.getenv('RDS_HOST')
    db_name = 'fdbt'
    # username = ssm_client.get_parameter(
    #     Name='fdbt-rds-reference-data-username',
    #     WithDecryption=True
    # )['Parameter']['Value']
    # password = ssm_client.get_parameter(
    #     Name='fdbt-rds-reference-data-password',
    #     WithDecryption=True
    # )['Parameter']['Value']

    logger.info("Connection to RDS MySQL instance...")
    connection = pymysql.connect(
        '127.0.0.1', user='root', passwd='root', db=db_name, connect_timeout=5)

    logger.info("SUCCESS! Connection to RDS MySQL instance succeeded")
    return connection


def get_operators(data_dict):
    operators = data_dict['TransXChange']['Operators']['Operator']
    if not isinstance(operators, list):
        operators = [operators]

    return operators


def get_services_for_operator(data_dict, operator):
    services = data_dict['TransXChange']['Services']['Service']
    if not isinstance(services, list):
        services = [services]

    relevant_services = [service for service in services if service['RegisteredOperatorRef'] == operator['@id']]

    return relevant_services


def extract_data_for_tnds_operator_service_table(data_dict, operator, service):
    noc_code = operator['NationalOperatorCode'] if 'NationalOperatorCode' in operator else operator['OperatorCode']
    line_name = service['Lines']['Line']['LineName']
    start_date = service['OperatingPeriod']['StartDate']
    operator_short_name = operator['OperatorShortName']
    service_description = service['Description'] if 'Description' in service else ''

    return (noc_code, line_name, start_date, operator_short_name, service_description)

def insert_into_tnds_operator_service_table(cursor, data_dict, operator, service):
    (noc_code, line_name, start_date, operator_short_name, service_description) = extract_data_for_tnds_operator_service_table(data_dict, operator, service)
    print(noc_code, line_name, start_date, operator_short_name, service_description)
    query = "INSERT INTO tndsOperatorService (nocCode, lineName, startDate, operatorShortName, serviceDescription) VALUES (%s, %s, %s, %s, %s)"

    logger.info("Writing to tndsOperatorService table...")
    cursor.execute(query, (noc_code, line_name, start_date,
                           operator_short_name, service_description))
    operator_service_id = cursor.lastrowid

    logger.info(
        "SUCCESS! Data successfully inserted into tndsOperatorService table. Id for insert is {}".format(operator_service_id))
    return operator_service_id


def collect_journey_pattern_section_refs_and_info(raw_journey_patterns):
    logger.info("Collecting JourneyPatternSectionRefs...")
    journey_patterns = []
    for raw_journey_pattern in raw_journey_patterns:
        journey_pattern_info = {
            'direction':  raw_journey_pattern['Direction'] if 'Direction' in raw_journey_pattern else None,
            'destination_display': raw_journey_pattern['DestinationDisplay'] if 'DestinationDisplay' in raw_journey_pattern else None
        }
        raw_journey_pattern_section_refs = raw_journey_pattern['JourneyPatternSectionRefs']
        journey_patterns.append({
            'journey_pattern_info': journey_pattern_info,
            'journey_pattern_section_refs': raw_journey_pattern_section_refs
        })
    logger.info("Collected JourneyPatternSectionRefs for {} JourneyPatterns provided in the TNDS file".format(len(journey_patterns)))
    return journey_patterns


def collect_journey_patterns(data_dict, service):
    raw_journey_patterns = service['StandardService']['JourneyPattern']
    raw_journey_pattern_sections = data_dict['TransXChange'][
        'JourneyPatternSections']['JourneyPatternSection']

    if not isinstance(raw_journey_pattern_sections, list):
        raw_journey_pattern_sections = [raw_journey_pattern_sections]

    if not isinstance(raw_journey_patterns, list):
        raw_journey_patterns = [raw_journey_patterns]

    journey_patterns_section_refs_and_info = collect_journey_pattern_section_refs_and_info(
        raw_journey_patterns)

    logger.info("Collecting JourneyPatterns...")
    journey_patterns = []
    for journey_pattern in journey_patterns_section_refs_and_info:
        journey_pattern_section_refs = journey_pattern['journey_pattern_section_refs']
        if not isinstance(journey_pattern_section_refs, list):
            journey_pattern_section_refs = [journey_pattern_section_refs]
        journey_pattern_sections = []
        for journey_pattern_section_ref in journey_pattern_section_refs:
            for raw_journey_pattern_section in raw_journey_pattern_sections:
                selected_raw_journey_pattern_section = []
                if raw_journey_pattern_section['@id'] == journey_pattern_section_ref:
                    selected_raw_journey_pattern_section = raw_journey_pattern_section
                if len(selected_raw_journey_pattern_section) > 0:
                    section_info = {
                        'tnds_id': selected_raw_journey_pattern_section['@id'],
                        'direction':  selected_raw_journey_pattern_section['Direction'] if 'Direction' in selected_raw_journey_pattern_section else None,
                        'destination_display': selected_raw_journey_pattern_section['DestinationDisplay'] if 'DestinationDisplay' in selected_raw_journey_pattern_section else None
                    }
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
                        journey_pattern_timing_links.append(
                            journey_pattern_timing_link)
                    journey_pattern_sections.append(
                        journey_pattern_timing_links)

                    processed_journey_pattern = {
                        'journey_pattern_sections': journey_pattern_sections,
                        'journey_pattern_info': journey_pattern['journey_pattern_info']
                    }

        journey_patterns.append(processed_journey_pattern)

    logger.info("Collected and formatted JourneyPatternTimingLinks for {} JourneyPatterns".format(len(journey_patterns)))
    return journey_patterns


def iterate_through_journey_patterns_and_run_insert_queries(cursor, data_dict, operator_service_id, service):
    journey_patterns = collect_journey_patterns(data_dict, service)
    for journey_pattern in journey_patterns:
        journey_pattern_id = insert_into_tnds_journey_pattern_table(
                cursor, operator_service_id, journey_pattern['journey_pattern_info'])

        links = []
        for journey_pattern_section in journey_pattern['journey_pattern_sections']:
            for journey_pattern_timing_link in journey_pattern_section:
                links.append(journey_pattern_timing_link)

        insert_into_tnds_journey_pattern_link_table(
                    cursor, links, journey_pattern_id)


def insert_into_tnds_journey_pattern_table(cursor, operator_service_id, journey_pattern_info):
    query = "INSERT INTO tndsJourneyPattern (operatorServiceId, destinationDisplay, direction) VALUES (%s, %s, %s)"

    logger.info("Writing to tndsJourneyPattern table...")
    cursor.execute(query, (operator_service_id, journey_pattern_info['destination_display'], journey_pattern_info['direction']))
    journey_pattern_id = cursor.lastrowid

    logger.info(
        "SUCCESS! Data successfully inserted into tndsJourneyPattern table. Id for insert is {}".format(journey_pattern_id))
    return journey_pattern_id


def insert_into_tnds_journey_pattern_link_table(cursor, links, journey_pattern_id):
    values_placeholders = ','.join(['(%s, %s, %s, %s, %s, %s, %s)' for link in links])

    values = [(journey_pattern_id, link['from_atco_code'], link['from_timing_status'], link['to_atco_code'], link['to_timing_status'], link['run_time'], order) for order,link in enumerate(links)]
    
    query = "INSERT INTO tndsJourneyPatternLink (journeyPatternId, fromAtcoCode, fromTimingStatus, toAtcoCode, toTimingStatus, runtime, orderInSequence) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    logger.info("Writing to tndsJourneyPatternLink table...")
    cursor.executemany(query, values)
                            
    logger.info(
        "SUCCESS! Data successfully inserted into tndsJourneyPatternLink table")


def write_to_database(data_dict):
    try:
        connection = connect_to_database()
        operators = get_operators(data_dict)

        if len(operators) > 1:
            print('MULTIPLE OPERATORS')

        with connection.cursor() as cursor:
            connection.begin()

            for operator in operators:
                services = get_services_for_operator(data_dict, operator)

                for service in services:
                    operator_service_id = insert_into_tnds_operator_service_table(
                        cursor, data_dict, operator, service)
                    iterate_through_journey_patterns_and_run_insert_queries(
                        cursor, data_dict, operator_service_id, service)

            connection.commit()

    except Exception as e:
        connection.rollback()
        logger.error("ERROR! Unexpected error. Could not write to database")
        logger.error(e)
        raise e

    finally:
        connection.close()

def process_file(path, index):
    xmltodict_namespaces = {'http://www.transxchange.org.uk/': None}

    try:
        path_in_str = str(path)
        print(path_in_str)
        print(index)
        tree = ET.parse(open(path_in_str))
        xml_data = tree.getroot()
        xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
        data_dict = xmltodict.parse(
            xml_string, process_namespaces=True, namespaces=xmltodict_namespaces)

        logger.info("Starting write to database...")
        write_to_database(data_dict)
    except Exception as e:
        print('ERROR UPLOADING DATA')
        return {
            'file': str(path),
            'error': e
        }

def main():
    pathlist = Path('/Users/laurencejones/Projects/tfn/data/tnds').glob('**/*.xml')

    num_cores = multiprocessing.cpu_count()

    print(num_cores)

    results = Parallel(n_jobs=num_cores)(delayed(process_file)(path, index) for index, path in enumerate(pathlist))
    print(results)


def download_from_s3_and_write_to_db(s3_client, ssm_client, bucket, key, file_dir):
    xmltodict_namespaces = {'http://www.transxchange.org.uk/': None}

    s3_client.download_file(bucket, key, file_dir)
    logger.info("Downloaded S3 file, '{}' to '{}'".format(key, file_dir))
    tree = ET.parse(file_dir)
    xml_data = tree.getroot()
    xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
    data_dict = xmltodict.parse(
        xml_string, process_namespaces=True, namespaces=xmltodict_namespaces)

    logger.info("Starting write to database...")
    write_to_database(data_dict, ssm_client)
    logger.info(
        "SUCCESS! Succesfully wrote contents of '{}' from '{}' bucket to database.".format(key, bucket))


def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = unquote_plus(event['Records'][0]['s3']
                       ['object']['key'], encoding='utf-8')
    file_dir = '/tmp/' + key.split('/')[-1]

    s3_client = boto3.client('s3')
    ssm_client = boto3.client('ssm')

    try:
        download_from_s3_and_write_to_db(s3_client, ssm_client, bucket, key, file_dir)

    except Exception as e:
        logger.error(e)
        raise e

main()
