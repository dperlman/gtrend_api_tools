"""
Tests for date string functions using fixtures from date_string_fixtures.py.

This test file validates that the standardize_date_range_start function correctly
processes various date string formats and extracts the start date from date ranges.
"""
import pytest
from gtrend_api_tools.date_strings import standardize_date_range_start


class TestStandardizeDateRangeStart:
    """Test class for standardize_date_range_start function."""
    
    @pytest.mark.parametrize("test_case", range(10))
    def test_date_string_standardization(self, test_first_date_strings, test_case):
        """Test that standardize_date_range_start correctly processes various date string formats."""
        input_date_str, expected_output = test_first_date_strings[test_case]
        
        # Test the function
        actual_output = standardize_date_range_start(input_date_str)
        
        # Assert the result matches expectation
        assert actual_output == expected_output, \
            f"Failed for input '{input_date_str}': expected '{expected_output}', got '{actual_output}'"
