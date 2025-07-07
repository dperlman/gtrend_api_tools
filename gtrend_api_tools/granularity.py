from typing import Dict, Union, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from gtrend_api_tools.utils import load_config, _print_if_verbose, diff_hour, diff_day, diff_week, diff_month
from gtrend_api_tools.date_strings import parse_date_str
import math

class GranularityManager:
    """
    A class to manage granularity rules and calculations.
    
    This class provides functionality for:
    - Managing granularity rules from configuration
    - Determining granularity from time indices
    - Creating time indices
    - Calculating total units
    - Determining search granularity
    
    The rules are sorted by max_days in ascending order, with rules having
    max_days=None placed at the end.
    """
    def __init__(self, config: Optional[dict] = None, verbose: bool = True):
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
        self.verbose = True

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
            freq_str = str(index.freqstr)[0]
            return freq_str
        
        # If no frequency is set, try to infer from time differences
        # Convert PeriodIndex to DatetimeIndex if needed
        if isinstance(index, pd.PeriodIndex):
            index = index.to_timestamp()
        
        # Calculate time differences in nanoseconds
        time_diffs = np.diff(index.astype(np.int64))
        
        # Print debugging information
        _print_if_verbose("Unique time differences and their counts:", self.verbose)
        _print_if_verbose(pd.Series(time_diffs).value_counts(), self.verbose)
        
        # Use pandas value_counts instead of np.bincount for memory efficiency
        most_common_diff = pd.Series(time_diffs).value_counts().index[0]
        _print_if_verbose(f"Most common difference: {most_common_diff} nanoseconds", self.verbose)
        
        # Convert to timedelta and check
        td = pd.Timedelta(most_common_diff, unit='ns')
        _print_if_verbose(f"Converted to timedelta: {td}", self.verbose)
        
        # Find the first rule where the time difference is less than or equal to record_seconds
        for code, rule in self.rules.items():
            if td.total_seconds() <= rule['record_seconds']:
                return code
        
        # If no rule matches, return monthly (last resort)
        return 'M'

    def create_time_indices(
        self,
        start_dt: datetime,
        end_dt: datetime,
        granularity: str
    ) -> Tuple[pd.DatetimeIndex, pd.PeriodIndex]:
        """
        Create DateTimeIndex and PeriodIndex based on the given date range and granularity.
        
        Args:
            start_dt (datetime): Start date
            end_dt (datetime): End date
            granularity (str): Time granularity code ('h', 'D', 'W', 'M')
            
        Returns:
            Tuple[pd.DatetimeIndex, pd.PeriodIndex]: A tuple containing the DateTimeIndex and PeriodIndex
            
        Raises:
            ValueError: If granularity is not one of 'h', 'D', 'W', 'M'
        """
        if granularity not in self.rules:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
        
        hour_diff = diff_hour(start_dt, end_dt)
        days_diff = diff_day(start_dt, end_dt)
        weeks_diff = diff_week(start_dt, end_dt)
        months_diff = diff_month(start_dt, end_dt)

        if granularity == 'm':
            _print_if_verbose(f"Hours difference: {hour_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='min')
        elif granularity == 'e':
            _print_if_verbose(f"Hours difference: {hour_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='8min')
        elif granularity == 'n':
            _print_if_verbose(f"Hours difference: {hour_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='16min')
        elif granularity == 'h':
            _print_if_verbose(f"Hours difference: {hour_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='h')
        elif granularity == 'D':
            _print_if_verbose(f"Days difference: {days_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='D')
        elif granularity == 'W':
            _print_if_verbose(f"Weeks difference: {weeks_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt, end=end_dt, freq='W')
        elif granularity == 'M':
            _print_if_verbose(f"Months difference: {months_diff}", self.verbose)
            period_index = pd.period_range(start=start_dt.replace(day=1), end=end_dt, freq='M')
        else:
            raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(self.rules.keys())}")
        
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
        
        # Truncate any HH:MM:SS
        # start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        # end_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        # _print_if_verbose(f"Truncated dates to midnight: {start_dt} to {end_dt}", self.verbose)
        
        # Calculate the time range
        time_diff = end_dt - start_dt
        _print_if_verbose(f"Time difference: {time_diff}", self.verbose)
        
        # Determine granularity based on rules in order
        for code, rule in self.rules.items():
            # Check if we are on the last one, with no limit on max_hours
            if rule['max_hours'] == float('inf'):
                granularity = code
                max_units = float('inf')
                _print_if_verbose(f"Selected granularity {code} (no limit on max_hours)", self.verbose)
                break
            # Create timedelta object based on max_hours
            max_timedelta = timedelta(hours=rule['max_hours'])
            max_days_info = f", max_days: {rule.get('max_days')}" if 'max_days' in rule else ""
            _print_if_verbose(f"Rule {code} has max_hours: {rule['max_hours']}{max_days_info} -> timedelta: {max_timedelta}", self.verbose)
            
            # Apply the max_inclusive logic
            if rule['max_inclusive']:
                if time_diff <= max_timedelta:
                    granularity = code
                    max_units = rule['max_records']
                    _print_if_verbose(f"Selected granularity {code} (inclusive rule, time_diff={time_diff} <= max_timedelta={max_timedelta})", self.verbose)
                    break
            else:
                if time_diff < max_timedelta:
                    granularity = code
                    max_units = rule['max_records']
                    _print_if_verbose(f"Selected granularity {code} (exclusive rule, time_diff={time_diff} < max_timedelta={max_timedelta})", self.verbose)
                    break
        
        # Create appropriate DateTimeIndex and PeriodIndex based on granularity
        datetime_index, period_index = self.create_time_indices(start_dt, end_dt, granularity)
        
        return {
            "granularity": granularity,
            "datetime_index": datetime_index,
            "period_index": period_index,
            "max_units": max_units
        }
    
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