"""
Tests for granularity detection using the granularity_test_dates fixture, but using the API instance.

This test file validates that the API returns the correct number of rows and columns for various date ranges and granularities.
"""
import pytest
from datetime import datetime

API_TO_TEST = 'dummy_api'

@pytest.mark.parametrize('api_key,api_instance', [(API_TO_TEST, API_TO_TEST)], indirect=True)
class TestAPIGranularityDetection:
    """Test class for granularity detection using API instance and fixture data."""
    
    @pytest.mark.parametrize("granularity_test_case", range(13), indirect=True)
    def test_api_granularity_boundary(self, api_instance, granularity_manager, granularity_test_case, multiple_terms):
        """Test that each date range produces the expected granularity and row count."""
        test_name, start_date, end_date, expected_granularity, expected_rows = granularity_test_case
        nterms = 3
        term = multiple_terms[nterms]
        term_list = [i.strip().replace(' ', '_').lower() for i in term.split(',')]
        assert len(term_list) == nterms, f"Test Internal Sanity Check Error: Expected {nterms} terms, got {len(term_list)}"
        
        # Run the search
        api_instance.search(search_term=term_list, start=start_date, end=end_date)
        df = api_instance.dataframe
        
        
        # Check DataFrame shape and columns
        assert not df.empty, f"DataFrame is empty for test '{test_name}'"
        assert len(df.columns) == nterms, f"Expected {nterms} columns, got {len(df.columns)} for test '{test_name}'"
        for term_name in term_list:
            assert term_name in df.columns, f"Column '{term_name}' missing in DataFrame for test '{test_name}'"
        assert len(df) == expected_rows, f"Row count {len(df)} does not match expected {expected_rows} for test '{test_name}'"


class TestGranularityBoundaryConditions:
    """Test class for boundary conditions and edge cases."""
    
    def test_one_minute_max_boundary(self, granularity_manager, granularity_test_dates):
        """Test the maximum boundary for one-minute granularity."""
        date_range = granularity_test_dates['one_minute_max']
        start_date = date_range['start']
        end_date = date_range['end']
        expected_granularity = date_range['granularity']
        
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        
        assert result['granularity'] == expected_granularity, \
            f"Expected '{expected_granularity}', got '{result['granularity']}'. " \
            f"Date range: {start_date} to {end_date}"
    
    def test_eight_minute_min_boundary(self, granularity_manager, granularity_test_dates):
        """Test the minimum boundary that triggers eight-minute granularity."""
        date_range = granularity_test_dates['eight_minute_min']
        start_date = date_range['start']
        end_date = date_range['end']
        expected_granularity = date_range['granularity']
        
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        
        assert result['granularity'] == expected_granularity, \
            f"Expected '{expected_granularity}', got '{result['granularity']}'. " \
            f"Date range: {start_date} to {end_date}"
    
    def test_daily_max_boundary(self, granularity_manager, granularity_test_dates):
        """Test the maximum boundary for daily granularity."""
        date_range = granularity_test_dates['daily_max']
        start_date = date_range['start']
        end_date = date_range['end']
        expected_granularity = date_range['granularity']
        
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        
        assert result['granularity'] == expected_granularity, \
            f"Expected '{expected_granularity}', got '{result['granularity']}'. " \
            f"Date range: {start_date} to {end_date}"
    
    def test_weekly_min_boundary(self, granularity_manager, granularity_test_dates):
        """Test the minimum boundary that triggers weekly granularity."""
        date_range = granularity_test_dates['weekly_min']
        start_date = date_range['start']
        end_date = date_range['end']
        expected_granularity = date_range['granularity']
        
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        
        assert result['granularity'] == expected_granularity, \
            f"Expected '{expected_granularity}', got '{result['granularity']}'. " \
            f"Date range: {start_date} to {end_date}"
    
    def test_monthly_extended_range(self, granularity_manager, granularity_test_dates):
        """Test a very long range that should use monthly granularity."""
        date_range = granularity_test_dates['monthly_extended']
        start_date = date_range['start']
        end_date = date_range['end']
        expected_granularity = date_range['granularity']
        
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        
        assert result['granularity'] == expected_granularity, \
            f"Expected '{expected_granularity}', got '{result['granularity']}'. " \
            f"Date range: {start_date} to {end_date}"


class TestGranularityTransitions:
    """Test class for granularity transitions between levels."""
    
    @pytest.mark.parametrize("granularity_transition_case", range(6), indirect=True)
    def test_granularity_transitions(self, granularity_manager, granularity_test_dates, granularity_transition_case):
        """Test transitions between granularity levels."""
        test_name_1, test_name_2, expected_1, expected_2 = granularity_transition_case
        
        # Test first granularity level
        date_range_1 = granularity_test_dates[test_name_1]
        start_date_1 = date_range_1['start']
        end_date_1 = date_range_1['end']
        result = granularity_manager.calculate_search_granularity(start_date_1, end_date_1)
        assert result['granularity'] == expected_1, \
            f"Transition test failed: {test_name_1} should be {expected_1}, got {result['granularity']}"
        
        # Test second granularity level (next step up)
        date_range_2 = granularity_test_dates[test_name_2]
        start_date_2 = date_range_2['start']
        end_date_2 = date_range_2['end']
        result = granularity_manager.calculate_search_granularity(start_date_2, end_date_2)
        assert result['granularity'] == expected_2, \
            f"Transition test failed: {test_name_2} should be {expected_2}, got {result['granularity']}"


class TestGranularityConsistency:
    """Test class for consistency checks across granularity levels."""
    
    def test_granularity_rules_consistency(self, granularity_manager):
        """Test that granularity rules are consistent with the fixture expectations."""
        rules = granularity_manager.rules
        
        # Check that all expected granularities exist in rules
        expected_granularities = ['m', 'e', 'n', 'h', 'D', 'W', 'M']
        for granularity in expected_granularities:
            assert granularity in rules, f"Granularity '{granularity}' not found in rules"
        
        # Check that max_records values are reasonable
        for granularity, rule in rules.items():
            assert 'max_records' in rule, f"max_records missing for granularity '{granularity}'"
            assert rule['max_records'] > 0, f"max_records must be positive for granularity '{granularity}'"
    
    def test_fixture_coverage(self, granularity_test_dates):
        """Test that the fixture covers all granularity levels."""
        granularities_in_fixture = set()
        for date_range in granularity_test_dates.values():
            granularities_in_fixture.add(date_range['granularity'])
        
        expected_granularities = {'m', 'e', 'n', 'h', 'D', 'W', 'M'}
        assert granularities_in_fixture == expected_granularities, \
            f"Fixture missing granularities: {expected_granularities - granularities_in_fixture}" 