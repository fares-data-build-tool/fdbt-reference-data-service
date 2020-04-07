import xmltodict
import json
import xml.etree.ElementTree as ET

filepath = '/Users/dannydavies/Documents/tfn/fares-data-build-tool/fdbt-reference-data-service/src/uploaders/tests/helpers/test_data/mock_tnds.xml'

# def get_journey_pattern_timing_link(raw)

def get_xml_as_json(filepath):
    tree = ET.parse(filepath)
    xml_data = tree.getroot()
    xml_string = ET.tostring(xml_data, encoding='utf-8', method='xml')
    data_dict = xmltodict.parse(xml_string, process_namespaces=True, namespaces={'http://www.transxchange.org.uk/': None})
    # Below are all lists but need to be converted to be a python list
    stop_points = data_dict['TransXChange']['StopPoints']['AnnotatedStopPointRef']
    raw_journey_pattern_sections = data_dict['TransXChange']['JourneyPatternSections']['JourneyPatternSection']
    operators = data_dict['TransXChange']['Operators']['Operator']
    services = data_dict['TransXChange']['Services']['Service']
    raw_journey_patterns = data_dict['TransXChange']['Services']['Service']['StandardService']['JourneyPattern']
    vehicle_journeys = data_dict['TransXChange']['VehicleJourneys']['VehicleJourney']

    journey_pattern_section_refs = []
    for raw_journey_pattern in raw_journey_patterns:
        raw_journey_pattern_section_refs = raw_journey_pattern['JourneyPatternSectionRefs']
        journey_pattern_section_refs.append(raw_journey_pattern_section_refs)

    journey_patterns = []
    for journey_pattern in journey_pattern_section_refs:
        if not isinstance(journey_pattern, list):
            journey_pattern = [journey_pattern]
        journey_pattern_sections = []
        for journey_pattern_section_ref in journey_pattern:
            for raw_journey_pattern_section in raw_journey_pattern_sections:
                selected_raw_journey_pattern_section = []
                if raw_journey_pattern_section['@id'] == journey_pattern_section_ref:
                    selected_raw_journey_pattern_section = raw_journey_pattern_section
                if len(selected_raw_journey_pattern_section) > 0:
                    raw_journey_pattern_timing_links = selected_raw_journey_pattern_section['JourneyPatternTimingLink']
                    if not isinstance(raw_journey_pattern_timing_links, list):
                        raw_journey_pattern_timing_links = [raw_journey_pattern_timing_links]
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
    print(journey_patterns)

    # print(json.dumps(journey_patterns, indent=4))
    # print(journey_pattern_sections)
    # print(json.dumps(journey_pattern_sections[0], indent=4))

get_xml_as_json(filepath)