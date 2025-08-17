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



@pytest.fixture(scope="module")
def compound_batch_spec_list(request, simple_test_cases):
    """A list of lists of SearchSpec objects.
    
    Creates a list of lists of SearchSpec objects,
    using simple_test_cases in sequence. If more specs are needed
    than available test cases, it cycles through the test cases.
    The number of lists and the number of specs per list are controlled via request.param from
    pytest.mark.parametrize.
    request.param should be a tuple of (number_of_lists, number_of_specs_per_list).
    The api will be dummy_api. But if the tuple has a third element, it will provide the api name(s).
    If the tuple is (number_of_lists, number_of_specs_per_list, api_name), the api_name will be used for all lists.
    If the tuple is (number_of_lists, number_of_specs_per_list, [api_name1, api_name2, ...]),
    and the number of api_names is the same as the number of lists, the api_names will be used for the corresponding list.
    If the number of api_names is not the same as the number of lists, the names will be cycled through.
    """
    if not hasattr(request, 'param'):
        pytest.fail("spec_list fixture requires parameterization with (number_of_specs, api_name, [api_name1, api_name2, ...])")
    
    # Unpack the parameters
    if not isinstance(request.param, (list, tuple)):
        pytest.fail("spec_list fixture requires parameterization with (number_of_specs, api_name, [api_name1, api_name2, ...])")
    
    # Default to dummy_api if no api_name is provided
    api_list = ['dummy_api']
    
    if len(request.param) == 2:
        number_of_lists, number_of_specs_per_list = request.param
    elif len(request.param) == 3:
        number_of_lists, number_of_specs_per_list, api_list = request.param
    else:
        pytest.fail("spec_list fixture requires parameterization with (number_of_specs, api_name, [api_name1, api_name2, ...])")

    specs = _make_compound_batch_spec_list(number_of_lists, number_of_specs_per_list, api_list)
    
    return specs

