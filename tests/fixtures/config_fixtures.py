"""
Configuration-related test fixtures for gtrend_api_tools.
"""
import pytest

@pytest.fixture(scope="module")
def test_config():
    """Load test configuration."""
    from gtrend_api_tools.utils import load_config
    return load_config()

@pytest.fixture(scope="module")
def available_apis():
    """Load available APIs configuration."""
    from gtrend_api_tools.APIs.api_utils import load_api_config
    return load_api_config() 