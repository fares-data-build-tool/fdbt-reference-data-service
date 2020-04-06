import pytest
import boto3
from botocore.stub import Stubber

from src.uploaders.xml_uploader import xml_uploader_handler as xml_uploader
from src.uploaders.tests.helpers import xml_helpers
from src.uploaders.tests.helpers.test_data import test_data

mock_data_dict = xml_helpers.generate_mock_data_dict(xml_helpers.filepath)

@pytest.fixture
def s3_stub(autouse=True):
    with Stubber(xml_uploader.s3.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


class TestDatabaseInsertQuerying:
    def test_insert_methods_are_called_correct_number_of_times(self):
        # Tests for insert_into_tnds_journey_pattern_section_table
        pass


class TestDataCollectionFunctionality:
    def test_extract_data_for_tnds_operator_service_table(self, mock_data_dict):
        expected_operator_and_service_info = (
            'ANWE', '4', '2018-01-28', 'ANW', 'Macclesfield - Upton Priory Circular')
        assert xml_uploader.extract_data_for_tnds_operator_service_table(
            mock_data_dict) == expected_operator_and_service_info

    def test_collect_journey_pattern_section_refs(self):
        mock_raw_journey_patterns = mock_data_dict['TransXChange'][
            'Services']['Service']['StandardService']['JourneyPattern']
        assert xml_uploader.collect_journey_pattern_section_refs(
            mock_raw_journey_patterns) == test_data.expected_list_of_journey_pattern_section_refs

    def test_collect_journey_patterns(self):
        assert xml_uploader.collect_journey_patterns(mock_data_dict) == test_data.expected_list_of_journey_patterns


class TestWriteToDatabase:
    # Tests for write_to_database
    def test_connection_is_committed_and_closed_on_successful_queries(self):
        pass

    def test_connection_is_rolled_back_when_write_fails(self):
        # with pytest.raises(Exception):
        # write_to_database()
        pass


class TestHandler:
    # Tests for handler
    def test_handler_extracts_data_into_a_dictionary_from_the_downloaded_file(self, s3_stub):
        # Create mock S3 event and context
        s3_stub.add_response(
            'download_file',
            expected_params={'Bucket': 'test-bucket',
                             'Key': "test-key", "Filename": "/tmp/test-key"},
            service_response={},
        )
        pass

    def test_handler_throw_an_error_when_it_fails(self):
        # with pytest.raises(Exception):
        # handler()
        pass
