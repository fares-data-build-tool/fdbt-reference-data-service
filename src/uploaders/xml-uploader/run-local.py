import xmltodict
import json
import xml.etree.ElementTree as ET

filepath = '/Users/dannydavies/Documents/tfn/REAL_REF_DATA/TNDS/NW/NW_01_ANW_5_1.xml'

def get_xml_as_json(filepath):
    tree = ET.parse(filepath)
    xml_data = tree.getroot()
    xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
    data_dict = xmltodict.parse(xml_string, process_namespaces=True, namespaces={'http://www.transxchange.org.uk/': None})
    # Below are all lists but need to be converted to be a python list
    stop_points = data_dict['TransXChange']['StopPoints']['AnnotatedStopPointRef']
    journey_pattern_sections = data_dict['TransXChange']['JourneyPatternSections']['JourneyPatternSection']
    operators = data_dict['TransXChange']['Operators']['Operator']
    services = data_dict['TransXChange']['Services']['Service']
    vehicle_journeys = data_dict['TransXChange']['VehicleJourneys']['VehicleJourney']

    print(json.dumps(operators, indent=4))

get_xml_as_json(filepath)