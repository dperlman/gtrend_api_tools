"""
Main test configuration and fixture exports for gtrend_api_tools.
"""
import os
import pytest
from datetime import datetime, timedelta, timezone

# Import and re-export fixtures from submodules
from .fixtures.api_fixtures import API_TO_TEST, VERBOSE, api_key, api_instance
from .fixtures.config_fixtures import test_config, available_apis
from .fixtures.granularity_fixtures import granularity_api_1, granularity_api_2, api_instances_for_comparison, granularity_manager
from .fixtures.search_fixtures import test_terms, test_dates, multiple_terms, granularity_test_dates, granularity_test_case, granularity_transition_case, simple_test_cases
from .fixtures.date_string_fixtures import test_first_date_strings
from .fixtures.batch_fixtures import spec_list

def pytest_configure(config):
    """Print the current API being tested before running tests."""
    # print(f"\nRunning tests with API: {API_TO_TEST}\n")
    # this is wrong
    pass

# Re-export all fixtures
__all__ = [
    'API_TO_TEST',
    'VERBOSE',
    'api_key',
    'api_instance',
    'test_terms',
    'test_dates',
    'multiple_terms',
    'granularity_test_dates',
    'granularity_test_case',
    'granularity_transition_case',
    'granularity_manager',
    'test_config',
    'available_apis',
    'granularity_api_1',
    'granularity_api_2',
    'api_instances_for_comparison',
    'test_first_date_strings',
    'spec_list'
] 