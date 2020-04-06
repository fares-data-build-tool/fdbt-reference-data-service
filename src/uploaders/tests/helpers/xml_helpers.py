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