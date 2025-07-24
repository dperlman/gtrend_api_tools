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
from .fixtures.search_fixtures import test_terms, test_dates, multiple_terms, granularity_test_dates, granularity_test_case, granularity_transition_case
from .fixtures.date_string_fixtures import test_first_date_strings

# Test configuration
API_TO_TEST = 'dummy_api'  # Specify which API to test
VERBOSE = False  # Set to True to see detailed API output during tests

@pytest.fixture(scope="module")
def api_key(test_config, request, available_apis):
    """Get API key for the specified API."""
    if not hasattr(request, 'param'):
        pytest.fail("api_key fixture requires parameterization with API name")
    
    api_name = request.param
    # If the API doesn't require a key, return None
    if available_apis.get(api_name, {}).get('type') != 'paid':
        return None
    return test_config.get('api_keys', {}).get(api_name)

@pytest.fixture(scope="module")
def api_instance(api_key, available_apis, request):
    """Create an API instance for testing."""
    if not hasattr(request, 'param'):
        pytest.fail("api_instance fixture requires parameterization with API name")
    
    api_name = request.param
    
    # Check if API is paid and requires an API key
    if available_apis.get(api_name, {}).get('type') == 'paid' and not api_key:
        pytest.skip(f"No API key found for {api_name} in config")
    
    # Import the API class
    from gtrend_api_tools.APIs.api_utils import get_api_class
    
    ApiClass = get_api_class(api_name)
    
    return ApiClass(api_key=api_key, verbose=VERBOSE)

def pytest_configure(config):
    """Print the current API being tested before running tests."""
    print(f"\nRunning tests with API: {API_TO_TEST}\n")

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
    'test_first_date_strings'
] 