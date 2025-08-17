from gtrend_api_tools.search_specs import SearchSpec
from gtrend_api_tools.APIs import SerpApi, Serpwow, TrendsPy, SearchApi, ApplescriptSafari, DummyApi, Brightdata, Decodo
from gtrend_api_tools.api_utils import get_api_class
from gtrend_api_tools.utils import load_config

# Import the fixture functions and call them to get the data
from fixtures.search_fixtures import simple_test_case_list

API_TO_TEST = 'dummy_api'
BATCH_METHOD = "sequential"  # options are 'thread' or 'sequential'
MAX_WORKERS = 10

verbose = True


# Load configuration
config = load_config()
tor_control_password = config.get('tor', {}).get('control_password')
api_key = config.get('api_keys', {}).get(API_TO_TEST.lower())
api_class = get_api_class(API_TO_TEST)

# if API_TO_TEST.lower() == "trendspy":
#     # Add tor_control_password for Trendspy
#     api_instance = api_class(api_key=api_key, verbose=verbose, tor_control_password=tor_control_password)
# else:
#     api_instance = api_class(api_key=api_key, verbose=verbose)
api_instance = api_class(api_key=api_key, verbose=verbose, tor_control_password=tor_control_password)


# Create a list of search specifications for the batch
spec_list = [
    # First spec: different term, same date range
    SearchSpec(
        search_term=simple_test_case_list[0][1],
        range_str=simple_test_case_list[0][0],
        api=API_TO_TEST
    ),
    # Second spec: same term, different date range
    SearchSpec(
        search_term=simple_test_case_list[1][1],
        range_str=simple_test_case_list[1][0],
        api=API_TO_TEST
    ),
    # Third spec: different term, different date range
    SearchSpec(
        search_term=simple_test_case_list[2][1],
        range_str=simple_test_case_list[2][0],
        api=API_TO_TEST
    )
]

results = api_instance.search_batch(
    search_spec_list=spec_list,
    method=BATCH_METHOD,
    max_workers=MAX_WORKERS
)

# print(results)
print("internal_state_history:")
print(api_instance.internal_state_history)
#print(api_instance.data)
#print(api_instance.dataframe)

#print(results[0].dataframe)
