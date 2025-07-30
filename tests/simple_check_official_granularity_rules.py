from gtrend_api_tools.api_utils import get_api_class
from gtrend_api_tools.search_specs import SearchSpec, DateRange
from gtrend_api_tools.utils import load_config
from gtrend_api_tools.granularity import GranularityManager
from importlib import import_module
from datetime import timedelta, datetime
import pandas as pd

api_to_test = 'serpapi'
search_term = 'hamburger'
start_date = '2024-01-01'
start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
test_days = [7, 30, 90, 269, 270, 271, 1899, 1900, 1901]
verbose = False


config = load_config()
api_info = config.get('available_apis', {}).get(api_to_test)

# Check if the API is paid and retrieve API key if needed
if api_info.get('type') == 'paid':
    # Get API key for the specified API
    api_key = config.get('api_keys', {}).get(api_to_test)
    
    if not api_key:
        raise ValueError(f"No API key found for {api_to_test} in config")
    
    print(f"Using API key for {api_to_test}")
else:
    api_key = None
    print(f"{api_to_test} is a free API, no key required")

# Import the API class
module = import_module(f'gtrend_api_tools.APIs.{api_to_test}')
ApiClass = get_api_class(api_to_test)

# Create API instance
api_instance = ApiClass(api_key=api_key, verbose=verbose)

# Get list of date ranges
test_date_ranges = []
test_search_specs = []
for days in test_days:
    end_date_dt = start_date_dt + timedelta(days=days)
    test_date_range = DateRange(start_date_dt, end_date_dt)
    test_search_spec = SearchSpec(search_term, date_range=test_date_range)
    test_date_ranges.append(test_date_range)
    test_search_specs.append(test_search_spec)
    print(test_search_spec)

data = {'day': [], 'records': [], 'granularity': []}
for i, search_spec in enumerate(test_search_specs):
    api_instance.search(search_spec=search_spec)
    api_instance.standardize_data()
    api_instance.make_dataframe()
    days = test_days[i]
    records = len(api_instance.dataframe)
    granularity_manager = GranularityManager(config)
    granularity = granularity_manager.get_index_granularity(api_instance.dataframe.index)
    data['day'].append(days)
    data['records'].append(records)
    data['granularity'].append(granularity)

df = pd.DataFrame(data)

print(df)


