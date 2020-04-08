import os
import xmltodict
import json
import xml.etree.ElementTree as ET

dir_path = os.path.dirname(os.path.realpath(__file__))
filepath = dir_path + '/test_data/mock_tnds.xml'

def generate_mock_data_dict(filepath):
    tree = ET.parse(filepath)
    xml_data = tree.getroot()
    xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
    mock_data_dict = xmltodict.parse(xml_string, process_namespaces=True, namespaces={'http://www.transxchange.org.uk/': None})
    return mock_data_dict

def count_list_lengths(mock_journey_patterns):
    total_journey_patterns = 0
    total_journey_pattern_sections = 0
    total_journey_pattern_timing_links = 0
    for journey_pattern in mock_journey_patterns:
        total_journey_patterns += 1
        for journey_pattern_section in journey_pattern:
            total_journey_pattern_sections += 1
            for journey_pattern_timing_link in journey_pattern_section:
                total_journey_pattern_timing_links += 1
    return (total_journey_pattern_sections, total_journey_pattern_timing_links)