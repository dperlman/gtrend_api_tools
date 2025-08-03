"""
Tests for granularity detection using the granularity_test_dates fixture, but using the API instance.

This test file validates that the API returns the correct number of rows and columns for various date ranges and granularities.
"""
import pytest
from datetime import datetime
from dateparser import parse

API_TO_TEST = 'applescript_safari'

@pytest.mark.parametrize('api_instance', [API_TO_TEST], indirect=True)
class TestAPIGranularityDetection:
    """Test class for granularity detection using API instance and fixture data."""
    
    @pytest.mark.parametrize("granularity_test_case", range(14), indirect=True)
    def test_api_granularity_boundary(self, api_instance, granularity_manager, granularity_test_case, multiple_terms):
        """Test that each date range produces the expected granularity and row count."""
        test_name, start_date, end_date, expected_granularity, expected_rows = granularity_test_case
        nterms = 3
        term = multiple_terms[nterms]
        term_list = [i.strip().replace(' ', '_').lower() for i in term.split(',')]
        assert len(term_list) == nterms, f"Test Internal Sanity Check Error: Expected {nterms} terms, got {len(term_list)}"
        
        # Run the search
        api_instance.search(search_term=term_list, start=start_date, end=end_date)

        # Check the search result timestamps
        range_first_timestamp = parse(api_instance.search_result.data[0]['date'], settings={'TIMEZONE': 'UTC'}  )
        range_last_timestamp = parse(api_instance.search_result.data[-1]['date'], settings={'TIMEZONE': 'UTC'})
        assert range_first_timestamp < range_last_timestamp, f"Start timestamp is not before end timestamp for test '{test_name}'"
        assert range_first_timestamp is not None, f"Start timestamp is None for test '{test_name}'"
        assert range_last_timestamp is not None, f"End timestamp is None for test '{test_name}'"

        # Get the dataframe
        df = api_instance.dataframe
        
        
        # Check DataFrame shape and columns
        assert not df.empty, f"DataFrame is empty for test '{test_name}'"
        assert len(df.columns) == nterms, f"Expected {nterms} columns, got {len(df.columns)} for test '{test_name}'"
        for term_name in term_list:
            assert term_name in df.columns, f"Column '{term_name}' missing in DataFrame for test '{test_name}'"
        assert len(df) == expected_rows, f"Row count {len(df)} does not match expected {expected_rows} for test '{test_name}'"
        assert len(df) > 2, f"Row count {len(df)} is unreasonably small for test '{test_name}'"
