import time
import os
import re
import sys
import unicodedata
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable, Union, Dict, Tuple, Any, List
import yaml
from types import SimpleNamespace
import appdirs
import shutil
import importlib.resources
from pathlib import Path
from loguru import logger

# EMERGENCY DEBUGGING: Uncomment the following lines to enable TRACE level logging
# for debugging config loading issues. This will show all the TRACE level calls
# in load_config() that are normally filtered out.
# logger.remove()
# logger.add(sys.stderr, level="TRACE")

GRANULARITY_RULES_NAME = 'granularity_rules.yaml'
DEFAULT_CONFIG_NAME = 'default_config.yaml'

# Global config cache
_CONFIG = None

# This is here to remind us that we are actually doing this below, after defining load_config()
# _CONFIG = load_config()
# DEFAULT_MAX_WORKERS = _CONFIG.get('api_parameters', {}).get('all', {}).get('default_max_workers', 10)

def load_config() -> dict:
    """
    Load configuration from user config directory.
    If the file doesn't exist or is empty, copies default_config.yaml to user config directory.
    Also loads granularity_rules.yaml from the package config folder.
    
    Config file locations:
    1. User config: ~/.config/gtrend_api_tools/config.yaml
    2. Package default: gtrend_api_tools/config/default_config.yaml (copied to user config if needed)
    
    Granularity rules are loaded from:
    - gtrend_api_tools/config/granularity_rules.yaml
    
    The granularity rules in the config are sorted by max_days in ascending order.
    Rules with max_days=None are placed at the end.

    Raises:
        FileNotFoundError: If no config file is found in any of the expected locations
    """
    global _CONFIG
    
    # Return cached config if available
    if _CONFIG is not None:
        return _CONFIG
    
    logger.trace("=== Config Loading Debug ===")
    # Get user config directory
    config_dir = appdirs.user_config_dir('gtrend_api_tools')
    user_config_path = os.path.join(config_dir, 'config.yaml')
    logger.trace(f"User config path: {user_config_path}")
    
    # Create user config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # If user config doesn't exist or is empty, copy from package default
    if not os.path.exists(user_config_path) or os.path.getsize(user_config_path) == 0:
        logger.trace("User config doesn't exist or is empty, copying from package default")
        try:
            # Get the path to the default config file
            default_config_path = importlib.resources.files('gtrend_api_tools.config').joinpath(DEFAULT_CONFIG_NAME)
            logger.trace(f"Default config path: {default_config_path}")
            
            # Direct file copy
            import shutil
            shutil.copy2(default_config_path, user_config_path)
            logger.trace(f"Copied default config to {user_config_path}")
            
        except Exception as e:
            logger.trace(f"Error copying default config: {e}")
            raise FileNotFoundError(
                f"Failed to copy default config to user config directory: {e}\n"
                f"User config path: {user_config_path}"
            )
    
    # Load user config
    logger.trace("Loading user config...")
    with open(user_config_path, 'r') as f:
        config = yaml.safe_load(f)
    logger.trace("User config contents:")
    logger.trace(yaml.dump(config))
    
    # Load granularity rules from package config
    try:
        logger.trace("Loading granularity rules...")
        rules_path = importlib.resources.files('gtrend_api_tools.config').joinpath(GRANULARITY_RULES_NAME)
        with open(rules_path, 'r') as f:
            rules_config = yaml.safe_load(f)
            if rules_config and 'granularity_rules' in rules_config:
                config['granularity_rules'] = rules_config['granularity_rules']
                logger.trace("Successfully loaded granularity rules")
            if rules_config and 'api_granularity_overrides' in rules_config:
                config['api_granularity_overrides'] = rules_config['api_granularity_overrides']
                logger.trace("Successfully loaded api granularity overrides")
    except Exception as e:
        logger.trace(f"Failed to load granularity rules: {e}")
    
    logger.trace("Final config contents:")
    logger.trace(yaml.dump(config))
    logger.trace("=== End Config Loading Debug ===")
    
    # Cache the config
    _CONFIG = config
    
    return config


def _print_if_verbose(message: str, verbose: bool = False) -> None:
    """
    Print message only if verbose is True, prefixed with the caller's function name and its caller.
    If the caller is _print, uses the caller of _print instead.
    Only prints the caller names if they have changed from the last call.
    
    Args:
        message (str): The message to print
        verbose (bool): Whether to print the message
    """
    if verbose:
        import inspect
        
        # Initialize the last caller attributes if they don't exist
        if not hasattr(_print_if_verbose, 'last_caller'):
            _print_if_verbose.last_caller = None
        if not hasattr(_print_if_verbose, 'last_caller_caller'):
            _print_if_verbose.last_caller_caller = None
        
        # Get the caller's frame info
        caller = inspect.currentframe().f_back
        # Get the caller's function name
        caller_name = caller.f_code.co_name
        
        # If the caller is _print, get the caller of _print instead
        if caller_name == '_print':
            caller = caller.f_back
            caller_name = caller.f_code.co_name
        
        # Get the caller's caller
        caller_caller = caller.f_back
        caller_caller_name = caller_caller.f_code.co_name if caller_caller else "unknown"
        
        # Only print the caller names if they have changed
        if caller_name != _print_if_verbose.last_caller or caller_caller_name != _print_if_verbose.last_caller_caller:
            _print_if_verbose(f"\n[{caller_caller_name}] / [{caller_name}]")
            _print_if_verbose.last_caller = caller_name
            _print_if_verbose.last_caller_caller = caller_caller_name
            
        # Print the message
        print(message)

# Load config once at module level and extract common values.
# (We do this here instead of at the top because we need to define two functions first.)
# _CONFIG = load_config()
# DEFAULT_MAX_WORKERS = _CONFIG.get('api_parameters', {}).get('all', {}).get('default_max_workers', 10)


def _custom_mode(df: pd.DataFrame, axis: int = 1) -> pd.Series:
    """
    Calculate mode of a DataFrame, returning mean of modes if multiple exist.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        axis (int): Axis along which to calculate mode (0 for columns, 1 for rows)
        
    Returns:
        pd.Series: Series containing mode values (or mean of modes if multiple exist)
    """
    logger.trace(f"Calculating custom mode for DataFrame shape {df.shape}, axis={axis}")
    # Get modes using pandas mode()
    modes = df.mode(axis=axis)
    # Calculate mean of modes along the same axis
    result = modes.mean(axis=axis)
    logger.trace(f"Custom mode calculation complete, result shape: {result.shape}")
    return result

def _numbered_file_name(orig_name: str, n_digits: int = 3, path: Optional[str] = None) -> str:
    """
    Generate a numbered filename by finding the next available number in the directory.
    If filename ends with _i### pattern, use the next available number. If no number pattern exists,
    add _i### pattern with specified digits. Number of digits is enforced in both cases.
    
    Args:
        orig_name (str): The original filename
        n_digits (int): Number of digits to use for the counter. Defaults to 3
        path (str, optional): Directory path to search for existing files. Defaults to None (current directory)
        
    Returns:
        str: New filename with the next available number
    """
    logger.trace(f"Generating numbered filename for '{orig_name}', n_digits={n_digits}, path={path}")
    # Split the filename into base name and extension
    base_name, ext = os.path.splitext(orig_name)
    
    # Remove any existing _i### pattern to get the base name
    base_name = re.sub(r'_i\d+$', '', base_name)
    
    # Get all files in the specified directory
    search_path = path if path else '.'
    existing_files = [f for f in os.listdir(search_path) if os.path.isfile(os.path.join(search_path, f))]
    
    # Find the highest existing number
    max_number = 0
    pattern = re.compile(f"{base_name}_i(\\d+){ext}$")
    
    for file in existing_files:
        match = pattern.match(file)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
    
    # Use the next available number
    next_number = max_number + 1
    
    # Create the new filename with _i and enforced n_digits pattern
    new_name = f"{base_name}_i{next_number:0{n_digits}d}{ext}"
    
    if path:
        new_name = os.path.join(path, new_name)
    
    logger.trace(f"Generated numbered filename: '{new_name}' (next_number={next_number})")
    return new_name

def save_to_csv(
    combined_df: pd.DataFrame,
    search_term: str,
    path: Optional[str] = None,
    comment: Optional[str] = None
) -> str:
    """
    Save the dataframe to a CSV file.
    
    Args:
        combined_df (pd.DataFrame): The dataframe to save
        search_term (str): The search term used to generate the data
        path (Optional[str]): Directory path to save the file. Defaults to None (current directory)
        comment (Optional[str]): Comment to add at the top of the file. Defaults to None
        
    Returns:
        str: The filename that was created
    """
    logger.info(f"Saving DataFrame to CSV: shape={combined_df.shape}, search_term='{search_term}', path={path}")
    
    # Create a filename with the search term and current ISO date
    current_date = datetime.now().strftime("%Y-%m-%d")
    formatted_utc_gmtime = time.strftime("%Y-%m-%dT%H-%MUTC", time.gmtime())

    # Replace spaces with underscores in the search term for the filename
    safe_search_term = search_term.replace(" ", "_")
    filename = f"{safe_search_term}_at_{formatted_utc_gmtime}.csv"
    filename = _numbered_file_name(filename, path=path)
    
    # _numbered_file_name will handle the path if provided
    
    # First write the comment if provided
    if comment:
        logger.debug(f"Adding comment to CSV file: {comment}")
        with open(filename, 'w') as f:
            f.write(f"# {comment}\n")
    
    # Save the dataframe to the CSV file
    combined_df.to_csv(filename, index=True, mode='a')
    logger.info(f"Data successfully saved to {filename}")
    return filename

def _get_total_size(obj: Any, seen: Optional[set] = None) -> int:
    """
    Calculate the total memory size of an object, including all nested objects.
    
    Args:
        obj: The object to measure
        seen: Set of object IDs already seen (to prevent infinite recursion)
        
    Returns:
        int: Total size in bytes
    """
    logger.trace(f"Calculating total size for object type {type(obj).__name__}")
    if seen is None:
        seen = set()
        
    obj_id = id(obj)
    if obj_id in seen:
        return 0
        
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    
    # Handle different types of objects
    if isinstance(obj, dict):
        size += sum(_get_total_size(v, seen) + _get_total_size(k, seen) 
                   for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(_get_total_size(item, seen) for item in obj)
    elif hasattr(obj, '__dict__'):
        # Handle custom objects
        size += _get_total_size(obj.__dict__, seen)
    elif hasattr(obj, 'items'):
        # Handle pandas/numpy objects that have items() method
        size += sum(_get_total_size(v, seen) + _get_total_size(k, seen) 
                   for k, v in obj.items())
    
    logger.trace(f"Total size for {type(obj).__name__}: {size} bytes")
    return size


def diff_month(d1: datetime, d2: datetime) -> int:
    logger.trace(f"Calculating month difference: {d1} to {d2}")
    d2m = d2.replace(day=1) # replace the day of the month with the first day of the month
    d1m = d1.replace(day=1) # replace the day of the month with the first day of the month
    result = (d2m.year - d1m.year) * 12 + d2m.month - d1m.month
    logger.trace(f"Month difference result: {result}")
    return result

def diff_week(d1: datetime, d2: datetime) -> int:
    logger.trace(f"Calculating week difference: {d1} to {d2}")
    result = ((d2-d1).days // 7) # need to test to see if this is correct
    logger.trace(f"Week difference result: {result}")
    return result

def diff_day(d1: datetime, d2: datetime) -> int:
    logger.trace(f"Calculating day difference: {d1} to {d2}")
    result = (d2-d1).days
    logger.trace(f"Day difference result: {result}")
    return result

def diff_hour(d1: datetime, d2: datetime) -> int:
    logger.trace(f"Calculating hour difference: {d1} to {d2}")
    result = ((d2-d1).total_seconds() // 3600)
    logger.trace(f"Hour difference result: {result}")
    return result

def period_index_range_info(period_index: pd.PeriodIndex) -> dict:
    """
    Calculate the duration of a period index, without the 1 microsecond offset that pandas does by default.
    Use this with caution! This is what we want for most of our Google Trends purposes,
    but there are good reasons why Pandas Periods work this way normally.
    Args:
        period_index (pd.PeriodIndex): The period index to calculate the duration of.
    Returns:
        timedelta: The duration of the period index.
    """
    logger.trace(f"Calculating period index range info: length={len(period_index)}, freq={period_index.freq}")
    temp_period_index = period_index.union([period_index[-1] + 1])
    start_dt = temp_period_index[0].start_time
    end_dt = temp_period_index[-1].start_time
    duration = end_dt - start_dt
    num_periods = len(period_index)
    mean_period_duration = duration / num_periods
    result = {'start_dt': start_dt, 'end_dt': end_dt, 'duration': duration, 'num_periods': num_periods, 'mean_period_duration': mean_period_duration}
    logger.trace(f"Period index range info: {result}")
    return result

def datetime_index_range_info(datetime_index: pd.DatetimeIndex) -> dict:
    """
    Calculate the duration of a datetime index.
    Args:
        datetime_index (pd.DatetimeIndex): The datetime index to calculate the duration of.
    Returns:
        timedelta: The duration of the datetime index.
    """
    logger.trace(f"Calculating datetime index range info: length={len(datetime_index)}, freq={datetime_index.freq}")
    temp_datetime_index = datetime_index.union([datetime_index[-1] + 1])
    start_dt = temp_datetime_index[0]
    end_dt = temp_datetime_index[-1]
    duration = end_dt - start_dt
    num_periods = len(datetime_index)
    mean_period_duration = duration / num_periods
    result = {'start_dt': start_dt, 'end_dt': end_dt, 'duration': duration, 'num_periods': num_periods, 'mean_period_duration': mean_period_duration}
    logger.trace(f"Datetime index range info: {result}")
    return result


def get_module_logger(file_path):
    """Get a logger for a specific module"""
    # Extract just the module name (without path and extension)
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    logger.trace(f"Creating module logger for '{module_name}' from file '{file_path}'")
    return logger.bind(name=module_name)

def setup_logging(config):
    """Configure logging based on config settings"""
    # Remove default handler
    logger.remove()
    
    # Get format from config - if null or not specified, use None to get Loguru's default format with colors
    log_format = config["logging"].get("format")
    
    # Add main handler with default level
    main_level = config["logging"]["level"]
    main_handler_kwargs = {
        "sink": sys.stderr,
        "level": main_level,
        "colorize": True
    }
    if log_format is not None:
        main_handler_kwargs["format"] = log_format
    logger.add(**main_handler_kwargs)
    
    # Add file handler if specified
    if "file" in config["logging"]["handlers"]:
        # Determine log file path
        log_config = config["logging"].get("file", {})
        log_path = log_config.get("path")
        
        if log_path is None:
            # Use appdirs to get the default log directory
            config_dir = appdirs.user_config_dir('gtrend_api_tools')
            log_dir = os.path.join(config_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, 'gtrend_api_tools.log')
        else:
            # Use the explicitly specified path
            log_dir = os.path.dirname(log_path)
            if log_dir:  # If path includes directory
                os.makedirs(log_dir, exist_ok=True)
        
        # Add file handler with optional rotation
        file_kwargs = {
            "sink": log_path,
            "level": config["logging"]["level"]
        }
        if log_format is not None:
            file_kwargs["format"] = log_format
        
        # Capture rotation and retention settings
        rotation_setting = log_config.get("max_size")
        retention_setting = log_config.get("retention")
        
        # Add rotation if specified
        if rotation_setting:
            file_kwargs["rotation"] = rotation_setting
        if retention_setting:
            file_kwargs["retention"] = retention_setting
            
        logger.add(**file_kwargs)
    
    # Configure module-specific levels and formats using filters
    modules_config = config["logging"].get("modules", {})
    module_handlers_added = 0
    for module, module_config in modules_config.items():
        module_level = module_config.get("level")
        module_format = module_config.get("format")
        
        # Only add module-specific handler if level or format is specified
        if module_level is not None or module_format is not None:
            # Use module-specific values or fall back to defaults
            handler_level = module_level if module_level is not None else config["logging"]["level"]
            handler_format = module_format if module_format is not None else log_format
            
            module_handler_kwargs = {
                "sink": sys.stderr,
                "level": handler_level,
                "filter": lambda record: record["name"] == module,
                "colorize": True
            }
            if handler_format is not None:
                module_handler_kwargs["format"] = handler_format
            
            logger.add(**module_handler_kwargs)
            module_handlers_added += 1
    
    # Log setup completion at debug level
    logger.debug(f"Logging setup complete: {module_handlers_added} module-specific handlers added")
    
    # Log file settings if file logging was enabled
    if "file" in config["logging"]["handlers"]:
        logger.debug(f"File logging settings: rotation={rotation_setting}, retention={retention_setting}")

# Set up logging for the module automatically when utils is imported
def _auto_setup_logging():
    """Automatically set up logging when utils module is imported."""
    config = load_config()  # This won't have logging calls anymore
    setup_logging(config)

# Run the setup
_auto_setup_logging()

# Get module logger for utils.py itself
logger = get_module_logger(__file__)
