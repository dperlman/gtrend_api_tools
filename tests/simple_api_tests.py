import os
import sys

from gtrend_api_tools.APIs import SerpApi, Serpwow, TrendsPy, SearchApi, ApplescriptSafari, DummyApi, Brightdata
from datetime import datetime
from gtrend_api_tools.utils import load_config, _print_if_verbose
import json
import traceback

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
    # print(raw_data.keys())
    # print(len(raw_data['widgets']))
    # print(raw_data['widgets'][0].keys())
    #print(raw_data['widgets'][1])
    #print(len(raw_data['widgets'][0]['data']['default']['timelineData']))

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
    #print(f"Dataframe: {dataframe}")



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
    
    tor_control_password = config.get('tor', {}).get('control_password')

    start_date = "2024-01-01"
    end_date = "2024-01-07" # 6 days, gives hourly granularity
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

    print('config api_keys info:')
    print(config.get('api_keys', {}))
    # Initialize API instances with their respective keys
    # applescript_safari_instance = ApplescriptSafari(verbose=verbose, close_tabs=CLOSE_TABS)
    brightdata_instance = Brightdata(api_key=config.get('api_keys', {}).get('brightdata'), verbose=verbose)

    apis = [
        #{"name": "SerpApi", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Serpwow", "instance": None, "search_term": "coffee,tea"},
        #{"name": "SearchApi", "instance": None, "search_term": "coffee,tea"},
        #{"name": "ApplescriptSafari", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Brightdata", "instance": None, "search_term": "coffee,tea"},
        #{"name": "Scrapingdog", "instance": None, "search_term": "coffee,tea"},
        #{"name": "ApplescriptSafari", "instance": None, "search_term": "car,truck"},
        #{"name": "TrendsPy", "instance": None, "search_term": "coffee,tea"},
        {"name": "DummyApi", "instance": None, "search_term": "coffee,tea"}
    ]

    # Create API instances
    for api in apis:
        if api["instance"] is None:
            api_class = globals()[api["name"]]
            api_key = config.get('api_keys', {}).get(api["name"].lower())
            if api["name"].lower() == "trendspy":
                # Add tor_control_password for Trendspy
                api["instance"] = api_class(api_key=api_key, verbose=verbose, tor_control_password=tor_control_password)
            else:
                api["instance"] = api_class(api_key=api_key, verbose=verbose)

    # Test each API
    for api in apis:
        print(f"Testing {api['name']} with search term: {api['search_term']}")
        test_api(api["instance"], api["name"], start_date, end_date, api["search_term"], verbose)

    # Close all Safari tabs if we've tested ApplescriptSafari
    for api in apis:
        if api["name"].lower() == "applescriptsafari" and api["instance"] is not None:
            if api["instance"].search_history:
                print("Closing all Safari tabs")
                api["instance"]._close_all_safari_tabs()  # this is a method of the ApplescriptSafari class
                print("All Safari tabs closed")
    # Moved the closing logic inside the first loop as requested, and removed error handling.

if __name__ == "__main__":
    main() 
    