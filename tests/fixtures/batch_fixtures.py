"""
Batch-related test fixtures for gtrend_api_tools.
"""
import pytest
from gtrend_api_tools.search_specs import SearchSpec

@pytest.fixture(scope="module")
def spec_list(request, simple_test_cases):
    """Provide the spec list to use.
    
    Creates a list of SearchSpec objects of the given length,
    using simple_test_cases in sequence. If more specs are needed
    than available test cases, it cycles through the test cases.
    
    The number of specs and API name are controlled via request.param from
    pytest.mark.parametrize. request.param should be a tuple of (number_of_specs, api_name).
    """
    if not hasattr(request, 'param'):
        pytest.fail("spec_list fixture requires parameterization with (number_of_specs, api_name)")
    
    # Unpack the parameters
    if isinstance(request.param, (list, tuple)) and len(request.param) == 2:
        number_of_specs, api_name = request.param
    else:
        pytest.fail("spec_list fixture requires parameterization with (number_of_specs, api_name) tuple")
    
    specs = []
    
    for i in range(number_of_specs):
        # Cycle through simple_test_cases if needed
        test_case_idx = i % len(simple_test_cases)
        date_range_str, search_terms = simple_test_cases[test_case_idx]
        
        # Create SearchSpec from the test case
        spec = SearchSpec(
            search_term=search_terms,
            range_str=date_range_str,
            api=api_name
        )
        
        specs.append(spec)
    
    return specs

