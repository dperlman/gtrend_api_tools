import time
import os
from datetime import datetime, timedelta
from typing import Optional, Callable, Union, Dict, Any, List, Tuple
import pandas as pd
import yaml
import unicodedata
import re
from types import SimpleNamespace
from dateutil.parser import parse, ParserError
from gtrend_api_tools.utils import load_config, _print_if_verbose
from gtrend_api_tools.granularity import GranularityManager
import numpy as np


def get_api_class_name(file_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Get the class name for an API from its file name using the configuration.
    
    Args:
        file_name (str): The API file name (e.g., 'dummy_api.py')
        
    Returns:
        Optional[str]: The class name if found, None otherwise
    """
    if config is None:
        config = load_config()
    available_apis = config.get('available_apis', {})

    # Remove .py extension
    api_name = file_name.replace('.py', '')
    
    # Look up the API in the config
    if api_name in available_apis:
        return available_apis[api_name]['class']
    else:
        raise ValueError(f"get_api_class_name: API '{api_name}' not found in configuration")

def get_api_class(api_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get an API class from an API name.
    
    Args:
        api_name (str): The name of the API (e.g., 'serpapi', 'dummy_api')
        
    Returns:
        Any: The API class (not an instance)
        
    Raises:
        ValueError: If the API name is not found in configuration
        ImportError: If the API module cannot be imported
        AttributeError: If the API class cannot be found in the module
    """
    class_name = get_api_class_name(api_name, config)
    
    # Import the API module
    from importlib import import_module
    module = import_module(f'gtrend_api_tools.APIs.{api_name}')
    
    # Get the API class
    ApiClass = getattr(module, class_name)
    
    # Create and return the API instance
    return ApiClass

def api_string(api_class_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Get the API string identifier for this class from available_apis configuration.
    
    Returns:
        Optional[str]: The API string (e.g., 'serpapi', 'trendspy') or None if not found
    """
    # Search for the class name in the configuration
    if config is None:
        config = load_config()
    available_apis = config.get('available_apis', {})
    for api_string, api_info in available_apis.items():
        if api_info.get('class') == api_class_name:
            return api_string
    
    return None


def change_tor_identity(password: Optional[str], print_func: Optional[Callable] = None, control_port: Optional[int] = None) -> None:
    """
    Change the Tor identity by connecting to the Tor control port and sending a NEWNYM signal.
    Includes error handling and retry logic.
    
    Args:
        password (Optional[str]): Password for Tor control port
        print_func (Optional[Callable]): Function to use for printing debug information
        control_port (Optional[int]): Port number for Tor control port. If None, uses value from config.yaml
    """
    if print_func is None:
        print_func = print
        
    try:
        from stem.control import Controller
        from stem import Signal
    except ImportError:
        print_func("Error: stem library not installed. Please install it with 'pip install stem'")
        return
    
    if not password:
        print_func("Error: Tor control password not provided")
        return

    # Load control port from config if not provided
    if control_port is None:
        config = load_config()
        control_port = config.get('tor', {}).get('control_port', 9151)  # Default to 9151 if not found in config

    try:
        # Try to connect to the Tor control port
        with Controller.from_port(port=control_port) as controller:
            # Authenticate with the controller
            controller.authenticate(password=password)
            
            # Send the NEWNYM signal to change the identity
            controller.signal(Signal.NEWNYM)
            print_func("Tor identity changed successfully.")
            
            # Wait a moment to ensure the change takes effect
            time.sleep(2)
            
    except Exception as e:
        print_func(f"Error changing Tor identity: {e}")
        print_func("Make sure Tor is running with control port enabled.")
        print_func(f"Add 'ControlPort {control_port}' to your torrc file and restart Tor.")


def standard_dict_to_df(standardized_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert standardized dictionary format to a pandas DataFrame.
    
    Args:
        standardized_data (List[Dict[str, Any]]): List of dictionaries in standardized format,
            where each dict has 'date' and 'values' keys. The 'values' key contains a list of
            dicts with 'query' and 'value' keys.
            
    Returns:
        pd.DataFrame: DataFrame with dates as PeriodIndex and one column per search term.
            Column names are sanitized versions of the search terms.
    """
    # Create a dictionary to store the data
    data_dict = {}
    
    # Process each entry in the standardized data
    for entry in standardized_data:
        date = entry['date']
        for value_dict in entry['values']:
            query = value_dict['query']
            value = value_dict['value']
            
            # Sanitize the query name for use as a column name
            sanitized_query = query.replace(' ', '_').lower()
            
            # Add the value to the data dictionary
            if sanitized_query not in data_dict:
                data_dict[sanitized_query] = {}
            data_dict[sanitized_query][date] = value
    
    # Create DataFrame from the dictionary
    df = pd.DataFrame(data_dict)
    
    # Convert index to datetime if it's not already
    #print(df.index)
    df.index = pd.to_datetime(df.index, utc=True)
    
    # Get the frequency using GranularityManager
    granularity_manager = GranularityManager() # will load config automatically
    freq = granularity_manager.get_index_granularity(df.index)
    
    # print("Debugging df.index and freq from standard_dict_to_df:")
    # print(df.index)
    # print(freq)
    # Set the frequency on the index in case it isn't already explicitly set
    df.index.freq = freq
    
    # Sort by date
    df = df.sort_index()
    
    return df

def sinc_data(num_zero_crossings: int, max_value: float, min_value: float, num_points: int) -> np.ndarray:
    """
    Generate a sinc-like signal with specified parameters.
    
    Args:
        num_zero_crossings (int): Number of zero crossings on the positive axis only
        max_value (float): Maximum value of the signal
        min_value (float): Minimum value of the signal (will be at the edges)
        num_points (int): Number of points in the output array
        
    Returns:
        np.ndarray: Array of values following a sinc-like pattern
        
    Example:
        >>> data = sinc_data(2, 1.0, 0.0, 100)
        >>> # Returns array of length 100 with:
        >>> # - 2 zero crossings on positive axis
        >>> # - Maximum value of 1.0 at center
        >>> # - Minimum value of 0.0 at edges
    """
    # Create x values from -1 to 1
    x = np.linspace(-1, 1, num_points)
    
    # Scale x by number of zero crossings to fit more cycles
    x_scaled = x * num_zero_crossings
    
    # Generate sinc function
    # Add small epsilon to avoid division by zero
    epsilon = 1e-10
    y = np.sin(np.pi * x_scaled) / (np.pi * x_scaled + epsilon)
    
    # Scale to desired range
    # First scale to 0-1 range (except the first one)
    y = (y - -0.217233) / (y.max() - -0.217233) # this is always the global min value for the sinc function
    
    # Then scale to desired range
    y = y * (max_value - min_value) + min_value
    
    return y

# def file_name_to_class_name(file_name: str) -> str:
#     """
#     Convert a snake_case file name to a CamelCase class name.
#     Special handling for words ending in 'api' - the 'A' will be capitalized.
    
#     Args:
#         file_name (str): The file name in snake_case format (e.g. 'serp_api.py')
        
#     Returns:
#         str: The class name in CamelCase format (e.g. 'SerpApi')
#     """
#     # Remove .py extension if present
#     base_name = file_name.replace('.py', '')
    
#     # Split by underscore and process each word
#     words = base_name.lower().split('_')
    
#     # Process each word, handling special case for 'api'
#     processed_words = []
#     for word in words:
#         word = word.capitalize()
#         if word.endswith('api'):
#             word[-3] = word[-3].upper()
#         if word.endswith('py'):
#             word[-2] = word[-2].capitalize()
#         processed_words.append(word)
    
#     # Join words together
#     return ''.join(processed_words)

if __name__ == "__main__":
    test_strings = [
        "2020-01-01 - 2020-01-07",
        "2020-01-01 2020-01-07",
        "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07",
        "11/3/2021 - 11/10/2021",
        "Jan 1-7, 2020",
        "Jan 1 - 7, 2020",
        "Jan 1-Dec 7, 2020",
        "Jan 1 - Dec 7, 2020",
    ]
    for test_string in test_strings:
        print(f"Input: {test_string}")
        output = standardize_date_str(test_string, verbose=False)
        #print(output)
        print(f"Output: {output['formatted_range']['ymd']}")
