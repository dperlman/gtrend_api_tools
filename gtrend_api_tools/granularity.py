from typing import Dict, Union, Optional, Any, Tuple, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from gtrend_api_tools.utils import load_config, _print_if_verbose, diff_hour, diff_day, diff_week, diff_month, period_index_range_info
from gtrend_api_tools.date_strings import parse_date_str
import math

class GranularityManager:
    """
    A class to manage granularity rules and calculations.
    The actual rules are defined in the granularity_rules.yaml file.
    
    This class provides functionality for:
    - Managing granularity rules from configuration
    - Determining granularity from time indices
    - Creating time indices
    - Calculating total units
    - Determining search granularity
    
    The rules are sorted by max_days in ascending order, with rules having
    max_days=None placed at the end.
    """
    def __init__(self, config: Optional[dict] = None, verbose: bool = False):
        """
        Initialize granularity manager.
        
        Args:
            config (Optional[dict]): Configuration dictionary containing granularity rules. 
                                   If None, will load config automatically.
            verbose (bool): Whether to print debug information. Defaults to True.
        """
        if config is None:
            config = load_config()
        
        if not isinstance(config, dict):
            raise ValueError("config must be a dictionary")
        self.rules = config.get('granularity_rules', {})
        if not self.rules:
            raise ValueError("No granularity rules found in config")
        self.verbose = verbose


    def get_index_granularity(self, index: Union[pd.DatetimeIndex, pd.PeriodIndex]) -> str:
        """
        Determine the granularity of a pandas DateTimeIndex or PeriodIndex.
        
        Args:
            index (Union[pd.DatetimeIndex, pd.PeriodIndex]): The index to analyze
            
        Returns:
            str: The granularity code ('h' for hour, 'D' for day, 'W' for week, 'ME' for month end)
        """
        # Handle empty DataFrame or invalid index type
        if len(index) == 0 or not isinstance(index, (pd.DatetimeIndex, pd.PeriodIndex)):
            return None # it doesn't make sense to return a granularity code if we don't have any data
        if len(index) < 2:
            return None # it doesn't make sense to return a granularity code if there's only one data point
            
        # First try to get the frequency directly
        if index.freq is not None:
            freq_str = str(index.freqstr)
            return freq_str
        
        # Now try to use the native pandas method to get the frequency
        freq = index.inferred_freq
        if freq is not None:
            freq_str = str(freq)
            return freq_str
        
        # If neither of those worked, try to infer from time differences
        # Convert PeriodIndex to DatetimeIndex if needed
        if isinstance(index, pd.PeriodIndex):
            index = index.to_timestamp()
        
        # Calculate time differences in nanoseconds
        time_diffs = np.diff(index.astype(np.int64))
        time_diff_value_counts = pd.Series(time_diffs).value_counts()
        
        # Print debugging information
        _print_if_verbose("Unique time differences and their counts:", self.verbose)
        _print_if_verbose(time_diff_value_counts, self.verbose)
        
        # Use pandas value_counts instead of np.bincount for memory efficiency
        most_common_diff = time_diff_value_counts.index[0]
        _print_if_verbose(f"Most common difference: {most_common_diff} nanoseconds", self.verbose)
        
        # Convert to timedelta and check
        td = pd.Timedelta(most_common_diff, unit='ns')
        _print_if_verbose(f"Converted to timedelta: {td}", self.verbose)
        
        # Now get the granularity info and return it.
        ########################################################################################################################
        # This is actually completely wrong, going to have to fix this
        ########################################################################################################################
        return self.get_granularity_by_time_diff(td)['freq']
    

    def create_time_indices(
        self,
        start_dt: datetime,
        end_dt: datetime,
        granularity: str
    ) -> Tuple[pd.DatetimeIndex, pd.PeriodIndex]:
        """
        Create DateTimeIndex and PeriodIndex based on the given date range and granularity.
        
        The granularity rules and their corresponding frequencies are defined in the 
        granularity_rules.yaml configuration file.
        
        Args:
            start_dt (datetime): Start date
            end_dt (datetime): End date
            granularity (str): Time granularity code (e.g., 'm', 'e', 'n', 'h', 'D', 'W', 'M')
                             as defined in granularity_rules.yaml
            
        Returns:
            Tuple[pd.DatetimeIndex, pd.PeriodIndex]: A tuple containing the DateTimeIndex and PeriodIndex
            
        Raises:
            ValueError: If granularity is not found in the granularity_rules.yaml configuration
        """
        if granularity not in self.rules:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
        
        # Get the frequency from the granularity rules configuration
        if granularity not in self.rules:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
        
        freq = self.rules[granularity]['freq']
        _print_if_verbose(f"Using frequency '{freq}' for granularity '{granularity}'", self.verbose)
        
        # Create period index using the frequency from config
        period_index = pd.period_range(start=start_dt, end=end_dt, freq=freq)
        
        # make the datetime index from the period index, doing it this way
        # gives us something that matches how Google Trends does it
        datetime_index = period_index.to_timestamp()
        
        _print_if_verbose(f"Datetime index length: {len(datetime_index)}", self.verbose)
        _print_if_verbose(f"Period index length: {len(period_index)}", self.verbose)
        
        return datetime_index, period_index
    
    def calculate_total_units(
        self,
        start_dt: datetime,
        end_dt: datetime,
        granularity: str
    ) -> Dict[str, Union[int, pd.PeriodIndex]]:
        """
        Calculate the total number of time units between two dates for a given granularity.
        
        Args:
            start_dt (datetime): Start date
            end_dt (datetime): End date
            granularity (str): Time granularity code ('h', 'D', 'W', 'M')
            
        Returns:
            Dict[str, Union[int, pd.PeriodIndex]]: Dictionary containing:
                - num_periods: Total number of time units between the dates
                - period_index: The period index used for calculation
            
        Raises:
            ValueError: If granularity is not one of 'h', 'D', 'W', 'M'
        """
        if granularity not in self.rules:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
            
        period_index = pd.period_range(start=start_dt, end=end_dt, freq=granularity)
        _print_if_verbose(f"Created period index with {len(period_index)} periods for granularity {granularity}", self.verbose)
        #_print_if_verbose(f"Period index: {period_index}", self.verbose)
        
        return {
            'num_periods': len(period_index),
            'period_index': period_index
        }

    def calculate_search_granularity(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> Dict[str, Union[str, pd.DatetimeIndex, pd.PeriodIndex, int]]:
        """
        Calculate the appropriate granularity for a Google Trends search based on the time range
        and generate the corresponding DateTimeIndex and PeriodIndex.

        This takes start_date and end_date, truncates any HH:MM:SS, and then calculates the granularity based on the time range.

        Note: Although Google Trends allows (secretly, behind the scenes) for dates to be specified with hours for very short time ranges,
        we don't use this because it's not documented and it's not clear if it's reliable. We had to draw the line somewhere.
        New Note: that is not true. we are doing the full calculation.
        We are going to have to update this to do the longer time ranges correctly
        based on limit_units and limit_value.

        Args:
            start_date_dt (datetime): Start date of the search
            end_date_dt (datetime): End date of the search
            
        Returns:
            Dict[str, Union[str, pd.DatetimeIndex, pd.PeriodIndex, int]]: Dictionary containing:
                - "granularity": The appropriate granularity to use ("h" for hour, "D" for day, "W" for week, or "M" for month start)
                - "datetime_index": A pandas DateTimeIndex with the appropriate frequency
                - "period_index": A pandas PeriodIndex with the appropriate frequency
                - "max_units": The maximum number of units possible for the calculated granularity
        """
        # Convert strings to datetimes if necessary, using the CURRENT_DEFAULT_DT as the default (from utils.py)
        
        if isinstance(start_date, str): 
            start_dt = parse_date_str(start_date)
        else:
            start_dt = start_date
        if isinstance(end_date, str):
            end_dt = parse_date_str(end_date)
        else:
            end_dt = end_date
        
        # Calculate the time range
        time_diff = end_dt - start_dt
        week_diff = time_diff.days // 7
        day_diff = time_diff.days
        hour_diff = time_diff.seconds // 3600

        _print_if_verbose(f"Week difference: {week_diff}, day difference: {day_diff}, hour difference: {hour_diff}", self.verbose)
        
        return self.get_granularity_by_limit_units(start_dt, end_dt)
    

    def get_granularity_by_limit_units(
        self,
        start_dt: datetime,
        end_dt: datetime,
    ) -> str:
        """
        Get the granularity code for a given time difference using the limit_units and limit_value.
        """
        from gtrend_api_tools.date_strings import get_resolution_details
        # Determine granularity based on rules in order
        for code, rule in self.rules.items():
            search_resolution = rule.get('search_resolution')
            limit_units = rule.get('limit_units')
            limit_value = rule.get('limit_value')
            freq = rule.get('freq')
            max_records = rule.get('max_records')
            
            # Truncate start_dt and end_dt by the search_resolution
            res_args, _, _ = get_resolution_details(search_resolution)
            truncated_start = start_dt.replace(**res_args)
            truncated_end = end_dt.replace(**res_args)
            
            # Create a pandas PeriodIndex with freq=limit_units and the truncated dates
            #_print_if_verbose(f"Start: {truncated_start}, end: {truncated_end}, limit_units: {limit_units}, freq: {freq}", self.verbose)
            period_index = pd.period_range(start=truncated_start, end=truncated_end, freq=freq)
            num_periods = len(period_index)
            
            _print_if_verbose(f"Rule {code}: {num_periods} periods vs limit {limit_value}", self.verbose)
            
            # Stop when our number of periods is within the limit_value
            if num_periods <= max_records:
                _print_if_verbose(f"Selected granularity {code} ({num_periods} periods <= {max_records})", self.verbose)
                break
        
        # If we get here, return the one we left the loop on
        # If we got all the way to the end of the loop, we will return the last rule
        rule['granularity'] = code
        return rule


    def get_granularity_by_time_diff(
        self,
        time_diff: timedelta
    ) -> str:
        """
        Get the granularity code for a given time difference.
        NOTE: This is deprecated and will be removed in the future.
        Use get_granularity_by_limit_units instead.
        """ 
        # Determine granularity based on rules in order
        for code, rule in self.rules.items():
            # Check if we are on the last one, with no limit on max_hours
            if rule['max_hours'] == float('inf'):
                _print_if_verbose(f"Selected granularity {code} (no limit on max_hours)", self.verbose)
                break
            # Create timedelta object based on max_hours
            max_timedelta = timedelta(hours=rule['max_hours'])
            max_days_info = f", max_days: {rule.get('max_days')}" if 'max_days' in rule else ""
            _print_if_verbose(f"Rule {code} has max_hours: {rule['max_hours']}{max_days_info} -> timedelta: {max_timedelta}", self.verbose)
            
            # Apply the max_inclusive logic
            if rule['max_inclusive']:
                if time_diff <= max_timedelta:
                    _print_if_verbose(f"Selected granularity {code} (inclusive rule, time_diff={time_diff} <= max_timedelta={max_timedelta})", self.verbose)
                    break
            else:
                if time_diff < max_timedelta:
                    _print_if_verbose(f"Selected granularity {code} (exclusive rule, time_diff={time_diff} < max_timedelta={max_timedelta})", self.verbose)
                    break
        
        rule['granularity'] = code
        return rule
    


    def get_max_period_by_granularity(
        self,
        granularity: str,
        periods: int,
        start_dt: datetime
    ) -> Dict[str, Union[datetime, pd.PeriodIndex]]:
        """
        Get the maximum period for a given granularity, number of periods, and start date.
        
        Args:
            granularity (str): Time granularity code ('h', 'D', 'W', 'M')
            periods (int): Number of periods to calculate
            start_dt (datetime): Start date
            
        Returns:
            Dict[str, Union[datetime, pd.PeriodIndex]]: Dictionary containing:
                - start_dt: Start datetime
                - end_dt: End datetime
                - period_index: The period index spanning the range
        """
        _print_if_verbose(f"Calculating max period for granularity {granularity}, {periods} periods from {start_dt}", self.verbose)
        max_period_index = pd.period_range(start=start_dt, periods=periods, freq=granularity)
        end_dt = max_period_index.end_time[-1].round('s')
        _print_if_verbose(f"End datetime: {end_dt}", self.verbose)
        _print_if_verbose(f"Period index length: {len(max_period_index)}", self.verbose)
        
        return {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "period_index": max_period_index
        }
    
    def standardize_time_range(
        self,
        start: datetime = None,
        end: datetime = None, 
        granularity: str = 'D',
        range_space: str = ' '
    ) -> dict:
        """
        Convert start_date and end_date into formatted time range strings and set instance attributes.
        If dates are strings, they will be parsed into datetime objects.
        Every instance of DateRange should use this method to properly set its date or time range attributes.
        
        Args:
            start_date (Optional[Union[str, datetime]]): Start date. If string, will be parsed with dateutil.parser
            end_date (Optional[Union[str, datetime]]): End date. If string, will be parsed with dateutil.parser
            
        Returns:
            DateRange: Returns self for method chaining
            
        Raises:
            ValueError: If neither start_date nor end_date is provided
            ValueError: If self.granularity is not one of: 's' (seconds), 'm' (minutes), 'h' (hourly), 
                       'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'X' (decade)
        """
        # Check if any dates are provided
        if not start or not end:
            raise ValueError("make_time_range requires both start and end")

        # For clarity, get the rules we will use out of the config
        if granularity not in self.rules:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
        rule = self.rules[granularity]
        freq = rule['freq']
        fixed = rule['fixed']
        allows_hours = rule['allows_hours']
        allows_minutes = rule['allows_minutes']
        allows_seconds = rule['allows_seconds']
        
        if allows_seconds:
            format_str_ymd = "%Y-%m-%dT%H:%M:%S"
            format_str_mdy = "%m/%d/%YT%H:%M:%S"
            replace_keys = {'microsecond': 0}
        elif allows_minutes:
            format_str_ymd = "%Y-%m-%dT%H:%M"
            format_str_mdy = "%m/%d/%YT%H:%M"
            replace_keys = {'second': 0, 'microsecond': 0}
        elif allows_hours:
            format_str_ymd = "%Y-%m-%dT%H"
            format_str_mdy = "%m/%d/%YT%H"
            replace_keys = {'minute': 0, 'second': 0, 'microsecond': 0}
        else:
            format_str_ymd = "%Y-%m-%d"
            format_str_mdy = "%m/%d/%Y"
            replace_keys = {'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0}
        
        # Now do the truncation for datetime objects
        trimmed_start_date_dt = start.replace(**replace_keys)
        trimmed_end_date_dt = end.replace(**replace_keys)
        formatted_start_date_ymd = trimmed_start_date_dt.strftime(format_str_ymd)
        formatted_start_date_mdy = trimmed_start_date_dt.strftime(format_str_mdy)
        formatted_end_date_ymd = trimmed_end_date_dt.strftime(format_str_ymd)
        formatted_end_date_mdy = trimmed_end_date_dt.strftime(format_str_mdy)
        formatted_range_ymd = f"{formatted_start_date_ymd}{range_space}{formatted_end_date_ymd}"
        formatted_range_mdy = f"{formatted_start_date_mdy}{range_space}{formatted_end_date_mdy}"
        
        return {
            "trimmed_start_date_dt": trimmed_start_date_dt,
            "trimmed_end_date_dt": trimmed_end_date_dt,
            "formatted_start_date_ymd": formatted_start_date_ymd,
            "formatted_start_date_mdy": formatted_start_date_mdy,
            "formatted_end_date_ymd": formatted_end_date_ymd,
            "formatted_end_date_mdy": formatted_end_date_mdy,
            "formatted_range_ymd": formatted_range_ymd,
            "formatted_range_mdy": formatted_range_mdy
        }



