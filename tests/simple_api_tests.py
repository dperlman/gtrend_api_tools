import os
import sys

from gtrend_api_tools.APIs import SerpApi, Serpwow, TrendsPy, SearchApi, ApplescriptSafari, DummyApi, Brightdata, Decodo
from datetime import datetime
from gtrend_api_tools.utils import load_config
from gtrend_api_tools.api_utils import get_api_class, api_string
import json
import traceback

CLOSE_TABS = True # Close tabs after each search. This is useful for ApplescriptSafari, but not for other APIs.
#### Note that if we ever implement a corresponding browser-based API for Windows or Linux,
#### we will want to make sure to also add this option for those.

def test_api(
    api_instance, 
    api_name, 
    search_term, 
    start_date: str = None, 
    end_date: str = None, 
    range_str: str = None, 
    verbose: bool = True, 
    save_files: bool = False
):
    """Test an API instance with the specified parameters and save results to files.
    
    Args:
        api_instance: The API instance to test
        api_name: Name of the API being tested
        search_term: Search term(s) to test
        start_date: Start date for the search (optional)
        end_date: End date for the search (optional)
        range_str: Date range string (optional, alternative to start_date/end_date)
        verbose: Whether to print verbose output
        save_files: Whether to save results to files
    """
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
        range_str=range_str if range_str else None,
        verbose=verbose
    )
    raw_data = api_instance.raw_data
    # print(raw_data.keys())
    # print(len(raw_data['widgets']))
    # print(raw_data['widgets'][0].keys())
    #print(raw_data['widgets'][1])
    #print(len(raw_data['widgets'][0]['data']['default']['timelineData']))

    if save_files:
        # Save raw data to file
        # Convert results to formatted JSON strings
        raw_data_str = json.dumps(raw_data, indent=2, sort_keys=True)
        raw_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_raw.txt")
        with open(raw_output_file, 'w') as f:
            f.write(raw_data_str)
        print(f"Raw results saved to {raw_output_file}")
        

    standardized_data = api_instance.data
    #print(f"Standardized data: {standardized_data}")
    dataframe = api_instance.dataframe
    print(f"Dataframe columns: {dataframe.columns}")


    if save_files:
        # Save standardized data to file
        # Convert results to formatted JSON strings
        standardized_data_str = json.dumps(standardized_data, indent=2, sort_keys=True)
        standardized_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_standardized.txt")
        with open(standardized_output_file, 'w') as f:
            f.write(standardized_data_str)
        print(f"Standardized results ({len(standardized_data)} records) saved to {standardized_output_file}")
        
        # Save dataframe to file
        # Changed to use pandas DataFrame pickle method instead of CSV for saving
        dataframe_output_file = os.path.join('test_outputs', f"{api_name}_{search_term.replace(' ', '_')}_{current_time}_dataframe.pkl")
        dataframe.to_pickle(dataframe_output_file)
        print(f"Dataframe (pickled) saved to {dataframe_output_file}")

def main():
    # Load configuration
    config = load_config()
    
    # Get verbose flag from config or default to True
    # Actually this is just a test, so we'll set it to True for now.
    #verbose = config.get('verbose', False)
    verbose = True
    save_files = True
    
    tor_control_password = config.get('tor', {}).get('control_password')

    # ranges for testing sub-daily granularity
    # range_str = "2024-01-01T00 2024-01-01T04" # 4 hours
    # range_str = "2024-01-01T00 2024-01-01T05" # 5 hours
    # range_str = "2024-01-01T00 2024-01-02T11" # 35 hours
    # range_str = "2024-01-01T00 2024-01-02T12" # 36 hours
    # range_str = "2024-01-01T00 2024-01-03T23" # 71 hours
    # range_str = "2024-01-01T00 2024-01-04T00" # 72 hours
    # range_str = "2024-01-01T00 2024-01-07T23" # 191 hours
    # range_str = "2024-01-01T00 2024-01-08T00" # 192 hours
    # range_str = "2024-01-01T00 2024-01-09T23" # 263 hours
    # range_str = "2024-01-01T00 2024-01-10T00" # 264 hours
    # range_str = "2024-01-01T00 2024-01-11T23" # 335 hours
    
    # ranges for testing daily granularity
    # range_str = "2024-01-01 2024-01-01" # 1 day
    # range_str = "2024-01-01 2024-01-02" # 2 days
    # range_str = "2024-01-01 2024-01-03" # 3 days
    # range_str = "2024-01-01 2024-01-07" # 7 days
    range_str = "2024-01-01 2024-01-08" # 8 days
    # range_str = "2024-01-01 2024-01-09" # 9 days
    # range_str = "2024-01-01 2024-01-10" # 10 days (this one gives 10 output records maybe)
    # range_str = "2024-01-01 2024-01-30" # 30 days
    # range_str = "2024-01-01 2024-01-31" # 31 days
    # range_str = "2024-01-01 2024-02-01" # 31 days
    # range_str = "2024-01-01 2024-02-02" # 32 days
    # range_str = "2024-01-01 2024-02-03" # 33 days

    #range_start = "2024-01-01"
    #range_end = "2024-01-01"


    start_date = "2024-01-01"
    #end_date = "2024-01-01" # 1 day, gives very short daily granularity
    #end_date = "2024-01-09" # 9 days, gives very short daily granularity
    end_date = "2024-01-30" # 30 days, gives daily granularity
    #end_date = "2024-01-07" # 6 days, gives hourly granularity
    #end_date = "2024-09-26" # 265 days, gives daily granularity
    #end_date = "2029-03-14" # 1899 days, gives weekly granularity
    #end_date = "2029-03-15" # 1900 days, gives weekly granularity
    #end_date = "2029-03-16" # 1901 days, gives monthly granularity
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days_diff = (end_dt - start_dt).days
    print(f"\n{'='*50}")
    print(f"Start date: {start_date}, End date: {end_date}, Days difference: {days_diff}")
    print(f"{'='*50}")

    #print('config api_keys info:')
    #print(config.get('api_keys', {}))

    apis = [
        #{"name": "SerpApi", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Serpwow", "instance": None, "search_term": "coffee,tea"},
        #{"name": "SearchApi", "instance": None, "search_term": "coffee,tea"},
        #{"name": "ApplescriptSafari", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Brightdata", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Scrapingdog", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Decodo", "instance": None, "search_term": "coffee,tea"},
        #{"name": "ApplescriptSafari", "instance": None, "search_term": "car,truck"},
        #{"name": "TrendsPy", "instance": None, "search_term": "coffee,tea"},
        {"name": "DummyApi", "instance": None, "search_term": "coffee,tea"}
    ]

    # Create API instances
    for api in apis:
        if api["instance"] is None:
            api_class = get_api_class(api_string(api["name"]))
            api_key = config.get('api_keys', {}).get(api_string(api["name"]))
            if api_string(api["name"]) == "trendspy":
                # Add tor_control_password for Trendspy
                api["instance"] = api_class(api_key=api_key, verbose=verbose, tor_control_password=tor_control_password)
            else:
                api["instance"] = api_class(api_key=api_key, verbose=verbose)

    # Test each API
    for api in apis:
        print(f"Testing {api['name']} with search term: {api['search_term']}")
        # use this one for start_date/end_date  
        #test_api(api["instance"], api["name"], api["search_term"], start_date=start_date, end_date=end_date, verbose=verbose, save_files=save_files)
        # use this one for range_str
        test_api(api["instance"], api["name"], api["search_term"], range_str=range_str, verbose=verbose, save_files=save_files)

    # Close all Safari tabs if we've tested ApplescriptSafari
    for api in apis:
        if api["name"].lower() == "applescriptsafari" and api["instance"] is not None:
            if api["instance"].search_spec_history:
                print("Closing all Safari tabs")
                api["instance"]._close_all_safari_tabs()  # this is a method of the ApplescriptSafari class
                print("All Safari tabs closed")
    # Moved the closing logic inside the first loop as requested, and removed error handling.

if __name__ == "__main__":
    main() 
