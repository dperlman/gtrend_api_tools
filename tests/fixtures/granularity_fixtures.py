import pytest
from datetime import datetime
from gtrend_api_tools.granularity import GranularityManager

# Constants for granularity comparison
GRANULARITY_COMPARE_1 = 'dummy_api'
GRANULARITY_COMPARE_2 = 'dummy_api'

# Test configuration
LOG_LEVEL = 'INFO'  # Logging level for tests

@pytest.fixture(scope="module")
def granularity_manager(test_config):
    """Fixture providing a GranularityManager instance."""
    return GranularityManager(test_config, verbose=False)

@pytest.fixture(scope="module")
def granularity_api_1(available_apis):
    """Fixture to provide the first API for granularity comparison."""
    if GRANULARITY_COMPARE_1 in available_apis:
        return GRANULARITY_COMPARE_1
    pytest.skip(f"API {GRANULARITY_COMPARE_1} not available in available_apis")

@pytest.fixture(scope="module")
def granularity_api_2(available_apis):
    """Fixture to provide the second API for granularity comparison."""
    if GRANULARITY_COMPARE_2 in available_apis:
        return GRANULARITY_COMPARE_2
    pytest.skip(f"API {GRANULARITY_COMPARE_2} not available in available_apis")

@pytest.fixture(scope="module")
def api_instances_for_comparison(granularity_api_1, granularity_api_2, available_apis, test_config):
    """Create both API instances for side-by-side comparison using the same logic as api_instance fixture."""
    # Get the API names
    api1_name = granularity_api_1
    api2_name = granularity_api_2
    
    # Create both instances using the api_instance fixture
    from gtrend_api_tools.APIs import api_utils
    from importlib import import_module
    
    def create_api_instance(api_name):
        # Check if API is paid and requires an API key
        if available_apis.get(api_name, {}).get('type') == 'paid':
            api_key = test_config.get('api_keys', {}).get(api_name)
            if not api_key:
                pytest.skip(f"No API key found for paid {api_name} in config")
        else:
            api_key = None
        
        # Import the API class
        module = import_module(f'gtrend_api_tools.APIs.{api_name}')
        ApiClass = getattr(module, api_utils.get_api_class_name(f'{api_name}.py'))
        
        return ApiClass(api_key=api_key, verbose=LOG_LEVEL)
    
    return {
        'api1': create_api_instance(api1_name),
        'api2': create_api_instance(api2_name)
    } 