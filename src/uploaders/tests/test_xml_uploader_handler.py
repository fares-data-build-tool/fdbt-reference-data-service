import pytest
import mock
from moto import mock_s3, mock_ssm
import boto3

from tests.helpers import test_xml_helpers
from tests.helpers.test_data import test_data

mock_data_dict = test_xml_helpers.generate_mock_data_dict(
    test_xml_helpers.filepath)

class TestDatabaseInsertQuerying:
    def test_insert_methods_are_called_correct_number_of_times(self, s3):
        # Tests for insert_into_tnds_journey_pattern_section_table
        pass


class TestDataCollectionFunctionality:
    def test_extract_data_for_tnds_operator_service_table(self):
        from xml_uploader.xml_uploader_handler import extract_data_for_tnds_operator_service_table
        expected_operator_and_service_info = (
            'ANWE', '4', '2018-01-28', 'ANW', 'Macclesfield - Upton Priory Circular')
        assert extract_data_for_tnds_operator_service_table(
            mock_data_dict) == expected_operator_and_service_info

    def test_collect_journey_pattern_section_refs(self):
        from xml_uploader.xml_uploader_handler import collect_journey_pattern_section_refs
        mock_raw_journey_patterns = mock_data_dict['TransXChange'][
            'Services']['Service']['StandardService']['JourneyPattern']
        assert collect_journey_pattern_section_refs(
            mock_raw_journey_patterns) == test_data.expected_list_of_journey_pattern_section_refs

    def test_collect_journey_patterns(self):
        from xml_uploader.xml_uploader_handler import collect_journey_patterns
        assert collect_journey_patterns(
            mock_data_dict) == test_data.expected_list_of_journey_patterns


class TestMainFunctionality:
    # Tests for handler
    def test_handler_extracts_data_into_a_dictionary_from_the_downloaded_file(self, s3, ssm):
        from xml_uploader.xml_uploader_handler import download_from_s3_and_write_to_db
        conn = boto3.resource('s3', region_name='eu-west-2')
        conn.create_bucket(Bucket='test-bucket')
        mock_bucket = 'test-bucket'
        mock_key = 'test-key'

        download_from_s3_and_write_to_db(s3, ssm, mock_bucket, mock_key)
        pass

    def test_handler_throw_an_error_when_it_fails(self):
        with pytest.raises(Exception):
            xml_uploader.handler()
