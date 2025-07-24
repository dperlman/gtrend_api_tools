"""
Tests for granularity detection using the granularity_test_dates fixture.

This test file validates that the GranularityManager correctly determines
the appropriate granularity for various date ranges based on the rules
defined in granularity_rules.yaml.
"""
import pytest
from datetime import datetime


class TestGranularityDetection:
    """Test class for granularity detection using fixture data."""
    
    # @pytest.fixture(autouse=True)
    # def setup_test_data(self, granularity_test_dates):
    #     """Setup test data and count test cases."""
    #     self.num_test_cases = 0
    #     self.test_case_names = []
    #     for test_name, test_data in granularity_test_dates.items():
    #         # Validate the test cases are in the fixture
    #         assert 'start' in test_data
    #         assert 'end' in test_data
    #         assert 'granularity' in test_data
    #         assert 'expected_rows' in test_data
    #         self.num_test_cases += 1
    #         self.test_case_names.append(test_name)
    #     return self.num_test_cases
    
    @pytest.mark.parametrize("granularity_test_case", range(14), indirect=True)
    def test_granularity_boundary(self, granularity_manager, granularity_test_case):
        """Test that each date range produces the expected granularity."""
        test_name, start_date, end_date, expected_granularity, expected_rows = granularity_test_case
        
        # Calculate the granularity - let the granularity manager handle string conversion
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        actual_granularity = result['granularity']
        
        # Assert the granularity matches expectation
        assert actual_granularity == expected_granularity, \
            f"Test '{test_name}' failed: expected '{expected_granularity}', got '{actual_granularity}'. " \
            f"Date range: {start_date} to {end_date}"
                        
        # Verify the result contains the expected granularity rule fields
        assert 'granularity' in result
        assert 'name' in result
        assert 'freq' in result
        assert 'max_records' in result
        assert 'max_hours' in result
        assert 'max_days' in result
        assert 'max_inclusive' in result
        assert 'search_resolution' in result
        assert 'result_resolution' in result
        assert 'fixed' in result
        assert 'record_seconds' in result
        


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