import pytest
from datetime import datetime, timedelta
from gtrend_api_tools.granularity import GranularityManager
import pandas as pd
from typing import Optional
from tests.fixtures.granularity_fixtures import (
    api_instances_for_comparison,
    LOG_LEVEL
)

# Constants for granularity comparison
GRANULARITY_COMPARE_1 = 'dummy_api'
GRANULARITY_COMPARE_2 = 'dummy_api'

# Granularity test data
GRANULARITY_START_DATE = datetime(2010, 1, 1, 0, 0, 0)  # Fixed start date for all tests
GRANULARITY_DAY_DURATIONS = [6, 7, 8, 269, 270, 271, 1899, 1900, 1901]  # Test different durations

def id_func(param):
    """Generate test ID that includes granularity info"""
    if isinstance(param, str):  # api_name
        return param
    elif isinstance(param, tuple):  # (days, granularity)
        days, granularity = param
        return f"{days}days-{granularity}"
    else:  # days
        return f"{param}days"

# Test cases for different scenarios
TEST_CASES_DAYS = [7, 30, 90, 365]

@pytest.mark.parametrize("days", TEST_CASES_DAYS)
def test_record_count_consistency(api_instances_for_comparison, days):
    """
    Test that both APIs return consistent record counts for different day durations.
    
    Args:
        api_instances_for_comparison: Dictionary containing both API instances
        days (int): Number of days to test
    """
    api1 = api_instances_for_comparison['api1']
    api2 = api_instances_for_comparison['api2']
    
    end_date = GRANULARITY_START_DATE + timedelta(days=days)
    
    # Prepare search parameters
    search_params = {
        'search_term': "test",
        'start_date': GRANULARITY_START_DATE,
        'end_date': end_date
    }
    
    # Test first API
    api1.search(**search_params).standardize_data().make_dataframe()
    
    # Test second API
    api2.search(**search_params).standardize_data().make_dataframe()
    
    api1_records = len(api1.data)
    api2_records = len(api2.data)
    
    assert api1_records == api2_records, (
        f"APIs returned different record counts for {days} days: "
        f"{GRANULARITY_COMPARE_1}={api1_records}, {GRANULARITY_COMPARE_2}={api2_records}"
    )
    
    print(f"✓ {days} days: {api1_records} records")

@pytest.mark.parametrize("days", TEST_CASES_DAYS)
def test_granularity_consistency(api_instances_for_comparison, days):
    """
    Test that both APIs return consistent granularity for different day durations.
    
    Args:
        api_instances_for_comparison: Dictionary containing both API instances
        days (int): Number of days to test
    """
    api1 = api_instances_for_comparison['api1']
    api2 = api_instances_for_comparison['api2']
    
    end_date = GRANULARITY_START_DATE + timedelta(days=days)
    
    # Prepare search parameters
    search_params = {
        'search_term': "test",
        'start_date': GRANULARITY_START_DATE,
        'end_date': end_date
    }
    
    # Test first API
    api1.search(**search_params).standardize_data().make_dataframe()
    
    # Test second API
    api2.search(**search_params).standardize_data().make_dataframe()
    
    # Create GranularityManager for granularity detection
    from gtrend_api_tools.utils import load_config
    config = load_config()
    granularity_manager = GranularityManager(config)
    
    api1_granularity = granularity_manager.get_index_granularity(api1.dataframe.index)
    api2_granularity = granularity_manager.get_index_granularity(api2.dataframe.index)
    
    assert api1_granularity == api2_granularity, (
        f"APIs returned different granularities for {days} days: "
        f"{GRANULARITY_COMPARE_1}={api1_granularity}, {GRANULARITY_COMPARE_2}={api2_granularity}"
    )
    
    print(f"✓ {days} days: {api1_granularity} granularity") 