"""
Simple API granularity tests without pytest - importing test data from search_fixtures.
"""
from datetime import datetime, timezone 
from gtrend_api_tools.APIs import SerpApi, Serpwow, TrendsPy, SearchApi, ApplescriptSafari, DummyApi, Brightdata
from gtrend_api_tools.utils import load_config, _print_if_verbose
from gtrend_api_tools.api_utils import get_api_class
import json
import traceback
import os, sys

# Import the fixture functions and call them to get the data
from fixtures.search_fixtures import granularity_test_dict

GRANULARITY_TEST_DATES = granularity_test_dict
API_TO_TEST = 'applescript_safari'
#CASES_TO_TEST = ['one_minute_max', 'eight_minute_min', 'eight_minute_max', 'sixteen_minute_min', 'sixteen_minute_max', 'hourly_min', 'hourly_max']
CASES_TO_TEST = ['weekly_min']
SEARCH_TERM = 'coffee,tea'
CLOSE_TABS = True # Close tabs after each search. This is useful for ApplescriptSafari, but not for other APIs.
#### Note that if we ever implement a corresponding browser-based API for Windows or Linux,
#### we will want to make sure to also add this option for those.


def test_api(api_instance, api_name, start_date, end_date, search_term, verbose: bool = True):
    """Test an API instance with the specified parameters and save results to files."""
    print(f"\n{'='*50}")
    print(f"Testing {api_name}")
    print(f"{'='*50}")
    
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create test_outputs directory if it doesn't exist
    os.makedirs('test_outputs', exist_ok=True)
    
    # Get both raw and standardized data
    api_instance.search(
        search_term=search_term,
        start=start_date if start_date else None,
        end=end_date if end_date else None,
        verbose=verbose
    )
    raw_data = api_instance.raw_data
    #raw_data_str = json.dumps(raw_data, indent=2, sort_keys=True)
    #print(f"Raw data: {raw_data_str[:1000]}\n...")

    # print(raw_data.keys())
    # print(len(raw_data['widgets']))
    # print(raw_data['widgets'][0].keys())
    #print(raw_data['widgets'][1])
    #print(len(raw_data['widgets'][0]['data']['default']['timelineData']))

    # # Save raw data to file
    # # Convert results to formatted JSON strings
    # raw_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_raw.txt")
    # with open(raw_output_file, 'w') as f:
    #     f.write(raw_data_str)
    # print(f"Raw results saved to {raw_output_file}")
    

    standardized_data = api_instance.data
    #print(f"Standardized data: {standardized_data}")
    dataframe = api_instance.dataframe
    #print(f"Dataframe: {dataframe}")



    # # Save standardized data to file
    # # Convert results to formatted JSON strings
    # standardized_data_str = json.dumps(standardized_data, indent=2, sort_keys=True)
    # standardized_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_standardized.txt")
    # with open(standardized_output_file, 'w') as f:
    #     f.write(standardized_data_str)
    # print(f"Standardized results ({len(standardized_data)} records) saved to {standardized_output_file}")
    
    # # Save dataframe to file
    # # Changed to use pandas DataFrame pickle method instead of CSV for saving
    # dataframe_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_dataframe.pkl")
    # dataframe.to_pickle(dataframe_output_file)
    # print(f"Dataframe (pickled) saved to {dataframe_output_file}")



def main():
    # Load configuration
    config = load_config()
    
    # Get verbose flag from config or default to True
    # Actually this is just a test, so we'll set it to True for now.
    #verbose = config.get('verbose', False)
    verbose = True
    
    tor_control_password = config.get('tor', {}).get('control_password')


    print(f"\n{'='*50}")
    print(f"API name: {API_TO_TEST}, Search term: {SEARCH_TERM}, cases to test: {CASES_TO_TEST}")
    print(f"{'='*50}")

    #print('config api_keys info:')
    #print(config.get('api_keys', {}))
    # Initialize API instances with appropriate key
    # Get the correct API class by name using our utility function
    
    api_class = get_api_class(API_TO_TEST)
    
    # Check if API is paid and requires an API key
    available_apis = config.get('available_apis', {})
    if available_apis.get(API_TO_TEST, {}).get('type') == 'paid':
        api_key = config.get('api_keys', {}).get(API_TO_TEST)
        if not api_key:
            raise ValueError(f"No API key found for paid API {API_TO_TEST} in config")
    else:
        api_key = None
    
    if API_TO_TEST == 'applescriptsafari':
        api_instance = api_class(verbose=verbose, close_tabs=CLOSE_TABS)
    elif API_TO_TEST == 'trendspy':
        api_instance = api_class(verbose=verbose, tor_control_password=tor_control_password)
    else:
        api_instance = api_class(api_key=api_key, verbose=verbose)
    print(f"API instance: {api_instance}")

    # Test each API
    for test_name in CASES_TO_TEST:
        test_data = GRANULARITY_TEST_DATES[test_name]
        start_date = test_data['start']
        end_date = test_data['end']
        expected_granularity = test_data['granularity']
        expected_rows = test_data['expected_rows']
        print(f"Testing {API_TO_TEST} with search term: {SEARCH_TERM} for {test_name}")
        test_api(api_instance, API_TO_TEST, start_date, end_date, SEARCH_TERM, verbose)
        #print(api_instance.data)
        # Print actual vs expected results
        actual_rows = len(api_instance.dataframe)
        actual_granularity = api_instance.search_spec.granularity if hasattr(api_instance, 'search_spec') and api_instance.search_spec else 'unknown'
        
        print(f"\n{'='*30} RESULTS {'='*30}")
        print(f"Test case: {test_name}")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Expected granularity: {expected_granularity} | Actual granularity: {actual_granularity}")
        print(f"Expected rows: {expected_rows} | Actual rows: {actual_rows}")
        
        # Check if they match with color coding
        if actual_granularity == expected_granularity:
            print(f"\033[94mGranularity match: ✓\033[0m")  # Blue for success
        else:
            print(f"\033[91mGranularity match: ✗\033[0m")  # Red for failure
            
        if actual_rows == expected_rows:
            print(f"\033[94mRows match: ✓\033[0m")  # Blue for success
        else:
            print(f"\033[91mRows match: ✗\033[0m")  # Red for failure
        print(f"{'='*70}\n")
        


    # Close all Safari tabs if we've tested ApplescriptSafari
    if API_TO_TEST == 'applescriptsafari':
        if api_instance.search_history:
            print("Closing all Safari tabs")
            api_instance._close_all_safari_tabs()  # this is a method of the ApplescriptSafari class
            print("All Safari tabs closed")



if __name__ == "__main__":
    main() 
    









# # Example usage:
# if __name__ == "__main__":
#     print("Testing GranularityManager with fixture data:")
#     print("=" * 60)
    
#     for test_name, test_data in GRANULARITY_TEST_DATES.items():
#         start_date = test_data['start']
#         end_date = test_data['end']
#         expected_granularity = test_data['granularity']
#         expected_rows = test_data['expected_rows']
        
#         # Calculate granularity using the manager
#         result = granularity_manager.calculate_search_granularity(start_date, end_date)
#         calculated_granularity = result['granularity']
        
#         # Check if they match
#         status = "✓ PASS" if calculated_granularity == expected_granularity else "✗ FAIL"
        
#         print(f"{test_name:20} | Expected: {expected_granularity} | Calculated: {calculated_granularity} | {status}")
#         print(f"{'':20} | Date range: {start_date} to {end_date}")
#         print(f"{'':20} | Expected rows: {expected_rows}")
#         print()
    
#     print("=" * 60)
#     print("Test completed!")
