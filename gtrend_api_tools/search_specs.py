"""
This module provides the DateRange class and the GtrendDateRange class.
The DateRange class is a base class for all date range operations.
The GtrendDateRange class is a subclass of DateRange that is used to handle Google Trends specific date ranges.
SearchSpec is a subclass of GtrendDateRange with an additional parameter search_term. It is used to handle all search requests.

The complete list of parameters used in all classes in this file is:

- start: The start date of the range. Can be a string or datetime object.
- end: The end date of the range. Can be a string or datetime object.
- range_str: A string representing the date range (e.g., "2023-01-01 2023-12-31").
    If provided, this takes precedence over `start` and `end`.
- range_space: The string to use between dates in the output formatted range.
- resolution: The resolution for formatting output strings. Valid values are s, m, h, D, M, Y.
    Used to format output strings in both ymd and mdy formats.
    The logic of this is defined in utils.py in the function get_resolution_details.
    's' gives outputs like '2023-01-01T00:00:00' and '01/01/2023T00:00:00'
    'm' gives outputs like '2023-01-01T00:00' and '01/01/2023T00:00'
    'h' gives outputs like '2023-01-01T00' and '01/01/2023T00'
    'D' gives outputs like '2023-01-01' and '01/01/2023'
    'M' gives outputs like '2023-01' and '01/2023'
    'Y' gives outputs like '2023' and '2023'
- freq: The frequency code for the date range (e.g., 'D' for daily, 'M' for monthly).
    This parameter is used in pandas PeriodIndex objects. The valid values are defined in pandas PeriodIndex.
    Relevant values for Google Trends date ranges are: min, 8min, 16min, h, D, W, M.
    But anything that PeriodIndex can interpret is valid here.
- granularity: The granularity of the date range. This is the Google Trends-specific granularity,
    which is related to the period freq of a pandas PeriodIndex object, but this parameter takes
    a specific set of single-letter values that define the relevant possible Google Trends result granularities.
    These are fully defined in the granularity_rules.yaml file.
    Current valid values are: m, e, n, h, D, W, M which correspond to the example freq values above.
All classes require either (`start` and `end`) or `range_str`. Additional requirements are:
- DateRange requires freq and resolution. Respective defaults are 'D' and 'h'.
- GtrendDateRange calculates granularity, freq, and resolution from the start and end dates.
- SearchSpec requires search_term. Missing search_term is an error.
"""

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any, List, Tuple
from dateutil.parser import parse, ParserError
from gtrend_api_tools.utils import load_config, _print_if_verbose, period_index_range_info, datetime_index_range_info
from gtrend_api_tools.date_strings import parse_date_str, split_date_range_str, cleanup_date_str, get_resolution_details # parse_date_str is a wrapper for dateutil.parser.parse where we set the default the way we want it
from gtrend_api_tools.granularity import GranularityManager
import pandas as pd
from types import SimpleNamespace


########################################################
# DateRange class. Base class for all date range classes.
########################################################

class DateRange:
    """
    A class to handle date range operations and standardization.

    Args:
        start (Optional[Union[str, datetime]]): The start date of the range. Can be a string or datetime object.
        end (Optional[Union[str, datetime]]): The end date of the range. Can be a string or datetime object.
        range_str (Optional[str]): A string representing the date range (e.g., "2023-01-01 2023-12-31").
            If provided, this takes precedence over `start` and `end`.
        freq (str): The frequency code for the date range (e.g., 'D' for daily, 'M' for monthly).
            Any frequency valid for pandas PeriodIndex is valid here. Defaults to 'D' (daily).
        resolution (Optional[str]): The resolution for formatting or rounding, if needed.
            Defaults to 'h'. (Note: not always used, but included for compatibility.)
        range_space (str): The string to use between dates in the output formatted range.
            Defaults to a single space.

    Notes:
        - If `range_str` is provided, it will be parsed to determine `start` and `end`.
        - If `start` or `end` are strings, they will be parsed into datetime objects.
        - If you want to use Google Trend specific granularities, use the GtrendDateRange class.
    """
    def __init__(
        self,
        start: Optional[Union[str, datetime]] = None,
        end: Optional[Union[str, datetime]] = None,
        range_str: Optional[str] = None,
        freq: str = 'D',
        resolution: Optional[str] = 'h',
        range_space: str = ' '
    ):
        self.original_start: Optional[str] = start
        self.original_end: Optional[str] = end
        self.original_range_str: Optional[str] = range_str
        self.freq: str = freq  # Defaults to daily frequency.
        self.resolution: str = resolution
        self.range_space: str = range_space
        self.original_start_str: Optional[str] = None
        self.original_end_str: Optional[str] = None
        self.original_start_dt: datetime
        self.original_end_dt: datetime
        # self.start_str: str
        # self.last_index_str: str
        # self.end_str: str
        self.start_dt: datetime
        self.last_index_dt: datetime
        self.end_dt: datetime
        # self.formatted_start_ymd: str
        # self.formatted_start_mdy: str
        # self.formatted_end_ymd: str
        # self.formatted_end_mdy: str
        # self.formatted_range_ymd: str
        # self.formatted_range_mdy: str
        self.period_index: pd.PeriodIndex
        self.num_periods: int
        self.duration: timedelta
        self.str: SimpleNamespace = SimpleNamespace()

        # First we need to sort out range_str, start, and end.
        self._init_range_str_start_end(range_str, start, end)

        # Now we have good self.original_start_dt and self.original_end_dt.
        # Now set up the internal detailed parameters we need
        self._init_date_range_info()

        # Get the resolution arguments and apply them to the start and end dates and range strings
        self._apply_resolution()

    # Private methods

    def _init_range_str_start_end(self, range_str: Optional[str], start: Optional[Union[str, datetime]], end: Optional[Union[str, datetime]]) -> None:
        """
        Sort out range_str, start, and end.
        If range_str is provided, it takes precedence over start and end.
        If range_str is not provided, start and end must be provided.
        If range_str is provided, it must be a valid date range string.
        If start and end are provided, they must be valid date strings or datetime objects.
        """
        # If we got a range_str, parse it into start_date and end_date.
        # This takes precedence over start_date and end_date.
        parse_errors = ''
        if range_str is not None:
            # Use range_str if provided
            start, end = self._parse_range_str(range_str)
            if not start:
                parse_errors += "fail parse start_date "
            if not end:
                parse_errors += "fail parse end_date "
            if parse_errors:
                parse_errors += f"from range_str: {range_str}"
                raise ValueError(f"Cannot initialize DateRange with given inputs: {parse_errors}")

        # Now we definitely have start_date and end_date.
        # We may need to parse them into datetime objects.
        # Note that if we are using someone else's datatime objects,
        # they may have timezone information that will lead to unexpected results
        # when used with Google Trends.

        # Note that if we get here, parse_errors is still empty.
        if isinstance(start, str):
            self.original_start_str = start
            self.original_start_dt = parse_date_str(start)
            if self.original_start_dt is None:
                parse_errors += f"invalid start: {start} "
        elif isinstance(start, (datetime, pd.Timestamp)):
            self.original_start_dt = start
        else:
            parse_errors += f"invalid start: {start} "

        if isinstance(end, str):
            self.original_end_str = end
            self.original_end_dt = parse_date_str(end)
            if self.original_end_dt is None:
                parse_errors += f"invalid end: {end} "
        elif isinstance(end, (datetime, pd.Timestamp)):
            self.original_end_dt = end
        else:
            parse_errors += f"invalid end: {end}"

        if parse_errors:
            raise ValueError(f"Cannot initialize DateRange with given inputs: {parse_errors}")

        # Once we get here, we have set original_start_dt and original_end_dt.
        # Original_start_str and original_end_str are set only if `start` and `end` were strings.
        # One last sanity check: we don't want to allow start_dt to be greater than end_dt
        # And while we're at it, let's just arbitrarily set the minimum to one second
        if self.original_end_dt - self.original_start_dt < timedelta(seconds=1):
            raise ValueError("DateRange end_dt must be greater than start_dt by at least one second")

    def _parse_range_str(self, range_str: str) -> None:
        """
        Parse a date range string into start and end date strings.
        
        Args:
            range_str (str): Date range string in format like "Dec 31, 2023 - Jan 6, 2024" or "Jan 7 - 13, 2024"
            verbose (bool): Whether to print verbose debug information

        """
        # First clean the unicode to ascii because some apis returns some weird unicode characters
        clean_range_str = cleanup_date_str(range_str)
        # split the date range string into start and end date
        start_str, end_str = split_date_range_str(clean_range_str)
        # print(start_str)
        # print(end_str)
        
        return start_str, end_str
    
    def _init_date_range_info(self) -> None:
        """
        Calculate the period_index, datetime_index, duration, num_periods, and mean_period_duration.
        Here we offload some of the work to the pandas PeriodIndex object.
        We also make a DatetimeIndex object from the PeriodIndex because it has timezone information.
        We will set our start_dt and end_dt properties to what the PeriodIndex calculates.
        The PeriodIndex will also help us get the duration, num_periods, and mean_period_duration.
        """
        # print(self.freq)
        # print(self.original_start_dt)
        # print(self.original_end_dt)
        self.period_index = pd.period_range(start=self.original_start_dt, end=self.original_end_dt, freq=self.freq)
        self.datetime_index = self.period_index.to_timestamp().tz_localize(timezone.utc)
        # print(self.datetime_index.freqstr)
        self.extended_period_index = self.period_index.union([self.period_index[-1] + 1])
        self.extended_datetime_index = self.extended_period_index.to_timestamp().tz_localize(timezone.utc)

        self.start_dt = self.datetime_index[0].to_pydatetime()
        # print(self.start_dt)
        # print(self.start_dt.tzinfo)
        self.last_index_dt = self.datetime_index[-1].to_pydatetime()
        # print(self.last_index_dt)
        # print(self.last_index_dt.tzinfo)
        self.end_dt = self.extended_datetime_index[-1].to_pydatetime()
        # print(self.end_dt)
        # print(self.end_dt.tzinfo)
        self.duration = self.end_dt - self.start_dt
        self.num_periods = len(self.period_index)
        self.mean_period_duration = self.duration / self.num_periods

        #self.range_info = period_index_range_info(self.period_index) 
        #self.range_info = datetime_index_range_info(self.datetime_index) 
    
        

    def _apply_resolution(self) -> None:
        """
        Apply the resolution to the start and end dates.
        NOTE AND TODO: When we change self.start_dt and self.end_dt here, does it change what the PeriodIndex would be?
        """
        res_args, format_str_ymd, format_str_mdy = get_resolution_details(self.resolution)
        #print(self.resolution, format_str_ymd)
        self.start_dt = self.start_dt.replace(**res_args)
        self.last_index_dt = self.last_index_dt.replace(**res_args)
        self.end_dt = self.end_dt.replace(**res_args)
        self.str.start_ymd = self.start_dt.strftime(format_str_ymd)
        self.str.start_mdy = self.start_dt.strftime(format_str_mdy)
        self.str.last_index_ymd = self.last_index_dt.strftime(format_str_ymd)
        self.str.last_index_mdy = self.last_index_dt.strftime(format_str_mdy)
        self.str.end_ymd = self.end_dt.strftime(format_str_ymd)
        self.str.end_mdy = self.end_dt.strftime(format_str_mdy)
        self.str.index_range_ymd = f"{self.str.start_ymd}{self.range_space}{self.str.last_index_ymd}"
        self.str.index_range_mdy = f"{self.str.start_mdy}{self.range_space}{self.str.last_index_mdy}"
        self.str.full_range_ymd = f"{self.str.start_ymd}{self.range_space}{self.str.end_ymd}"
        self.str.full_range_mdy = f"{self.str.start_mdy}{self.range_space}{self.str.end_mdy}"

    def __str__(self):
        return f"{self.__class__.__name__} {self.str.full_range_ymd}"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(start_date={self.str.start_ymd}, end_date={self.str.end_ymd}, "
                f"freq={self.freq}, range_space='{self.range_space}')")


########################################################
# GtrendDateRange class. Extends DateRange to handle Google Trends specific date ranges.
########################################################


class GtrendDateRange(DateRange):
    """
    A class to handle date range operations and standardization for Google Trends.
    
    This class extends DateRange and automatically calculates the appropriate granularity
    based on the date range using the granularity rules from the configuration.
    The freq and resolution are set appropriately based on the granularity.
    
    Note: This class does not accept a granularity parameter. It always automatically
    calculates the appropriate granularity. If you need to specify granularity explicitly,
    use the DateRange base class instead.
    """
    def __init__(self, *args, **kwargs):
        # Just make sure we are not receiving the arguments `granularity` or `freq` or `resolution`.
        if 'granularity' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `granularity`")
        if 'freq' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `freq`")
        if 'resolution' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `resolution`")
        # OK that's all. just go ahead with the initialization.
        # Additional parameters that are specific to GtrendDateRange
        # If gtrend_params is not provided, set it to an empty dictionary
        if 'gtrend_params' not in kwargs:
            kwargs['gtrend_params'] = {}
        self.gtrend_params = kwargs['gtrend_params']
        # Maybe if I were a better programmer I could handle this default more gracefully but this is what I'm doing for now.
        if 'override_hours' not in self.gtrend_params:
            self.gtrend_params['override_hours'] = False
        # Remove the gtrend_params from the kwargs
        kwargs.pop('gtrend_params')
        # Now call the base class __init__
        super().__init__(*args, **kwargs)

    # def _init_range_str_start_end(self, range_str: Optional[str], start: Optional[Union[str, datetime]], end: Optional[Union[str, datetime]]) -> None:
    #     """
    #     Since we are extending DateRange, we need to override this method to make sure we are
    #     not receiving the arguments `granularity` or `freq` or `resolution`.
    #     """
    #     super()._init_range_str_start_end(range_str, start, end)
        

    def _init_date_range_info(self) -> None:
        """
        Since this is GtrendDateRange, we need to calculate the granularity before we do anything else,
        then from that we get the freq and resolution.
        Then we can proceed to calculate the period_index, duration, num_periods, and mean_period_duration.
        Here we offload some of the work to the pandas PeriodIndex object.
        We will set our start_dt and end_dt properties to what the PeriodIndex calculates.
        The PeriodIndex will also give us the duration, num_periods, and mean_period_duration,
        with help from the utils.py function period_index_range_info.
        """
        self.granularity_manager = GranularityManager() # will load config automatically
        self.granularity_info = self.granularity_manager.calculate_search_granularity(
            start_date=self.original_start_dt,
            end_date=self.original_end_dt
        )
        #print(self.original_start_dt, self.original_end_dt)
        #print(self.granularity_info)
        self.granularity = self.granularity_info['granularity']
        self.freq = self.granularity_info['freq']
        self.resolution = self.granularity_info['result_resolution']
        self.search_resolution = self.granularity_info['search_resolution']
        super()._init_date_range_info()

    def _apply_resolution(self) -> None:
        """
        Apply the resolution to the start and end dates.
        Extends the base class method to also make a search_resolution version of the start and end dates.
        """
        # First do it the original way
        super()._apply_resolution()
        # Then also create search ranges to be used in gtrend api calls
        res_args, format_str_ymd, format_str_mdy = get_resolution_details(self.search_resolution)
        start_dt = self.start_dt.replace(**res_args)
        last_index_dt = self.last_index_dt.replace(**res_args)
        formatted_start_ymd = start_dt.strftime(format_str_ymd)
        formatted_start_mdy = start_dt.strftime(format_str_mdy)
        formatted_last_index_ymd = last_index_dt.strftime(format_str_ymd)
        formatted_last_index_mdy = last_index_dt.strftime(format_str_mdy)
        # These are the new properties we have, beyond the base class properties
        self.str.search_range_ymd = f"{formatted_start_ymd}{self.range_space}{formatted_last_index_ymd}"
        self.str.search_range_mdy = f"{formatted_start_mdy}{self.range_space}{formatted_last_index_mdy}"

    def __str__(self):
        return f"{self.__class__.__name__} {self.str.full_range_ymd} (granularity: {self.granularity})"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(start_date={self.str.start_ymd}, end_date={self.str.end_ymd}, "
                f"granularity={self.granularity})")


########################################################
# SearchSpec class. Extends GtrendDateRange to include search terms.
########################################################

class SearchSpec(GtrendDateRange):
    """
    A class that extends GtrendDateRange to include search terms.
    This class handles both date range and search terms for a single search operation.
    
    Can be initialized in multiple ways:
    1. With date parameters: SearchSpec("coffee,tea", start_date="2023-01-01", end_date="2023-12-31")
    2. With existing DateRange or GtrendDateRange: SearchSpec("coffee,tea", date_range=my_date_range)
    3. (Not Recommended) Using classmethod: SearchSpec._from_date_range(my_date_range, "coffee,tea")
    """
    def __init__(
        self,
        search_term: Union[str, List[str]],
        date_range: Optional[DateRange] = None,
        **kwargs
    ):
        """
        Initialize a SearchSpec instance.
        
        Args:
            search_term (Union[str, List[str]]): Search terms. If string, will be split on commas
            date_range (Optional[DateRange]): Pre-configured DateRange object. If provided, other date kwargs are ignored
            **kwargs: Arguments passed to DateRange constructor (start_date, end_date, granularity, verbose, range_space)
        """
        if date_range is not None:
            # Delegate to classmethod for date_range initialization
            new_instance = self.__class__._from_date_range(date_range, search_term, **kwargs)
            # Copy all attributes from the new instance
            self.__dict__.update(new_instance.__dict__)
        else:
            # Standard initialization path
            # Filter out search_term from kwargs before passing to DateRange
            date_kwargs = {k: v for k, v in kwargs.items() if k != 'search_term'}
            # Pass filtered kwargs to DateRange constructor
            super().__init__(**date_kwargs)
            
            # Initialize SearchSpec-specific attributes
            self._init_search_spec(search_term)
    
    def __str__(self):
        return f"SearchSpec {self.term_string} {self.str.full_range_ymd}"
    
    def __repr__(self):
        return f"SearchSpec(search_term={self.term_string}, start_date={self.str.start_ymd}, end_date={self.str.end_ymd}, granularity={self.granularity})"
    
    @classmethod
    def _from_date_range(cls, date_range: DateRange, search_term: Union[str, List[str]], **kwargs):
        """
        Create a SearchSpec instance from an existing DateRange.
        
        Args:
            date_range (DateRange): Existing DateRange instance
            search_term (Union[str, List[str]]): Search terms
            **kwargs: Additional arguments (like verbose)
            
        Returns:
            SearchSpec: New SearchSpec instance
        """
        if not isinstance(date_range, DateRange):
            raise ValueError("date_range must be a DateRange instance")
        
        # Create instance without calling __init__
        instance = cls.__new__(cls)
        
        # Copy the DateRange state directly instead of re-initializing
        # This avoids conflicts between range_str, start_date, and end_date
        instance.original_start = date_range.original_start
        instance.original_end = date_range.original_end
        instance.original_range_str = date_range.original_range_str
        instance.original_start_str = date_range.original_start_str
        instance.original_end_str = date_range.original_end_str
        instance.original_start_dt = date_range.original_start_dt
        instance.original_end_dt = date_range.original_end_dt
        # instance.start_str = date_range.start_str
        # instance.end_str = date_range.end_str
        # instance.start_dt = date_range.start_dt
        # instance.end_dt = date_range.end_dt
        instance.str.start_ymd = date_range.str.start_ymd
        instance.str.start_mdy = date_range.str.start_mdy
        instance.str.end_ymd = date_range.str.end_ymd
        instance.str.end_mdy = date_range.str.end_mdy
        instance.str.index_range_ymd = date_range.str.index_range_ymd
        instance.str.index_range_mdy = date_range.str.index_range_mdy
        instance.str.full_range_ymd = date_range.str.full_range_ymd
        instance.str.full_range_mdy = date_range.str.full_range_mdy
        instance.str.search_range_ymd = date_range.str.search_range_ymd
        instance.str.search_range_mdy = date_range.str.search_range_mdy
        instance.freq = date_range.freq
        instance.resolution = date_range.resolution
        instance.range_space = date_range.range_space
        instance.period_index = date_range.period_index
        instance.num_periods = date_range.num_periods
        instance.duration = date_range.duration
        instance.mean_period_duration = date_range.mean_period_duration
        
        # Initialize SearchSpec-specific attributes
        instance._init_search_spec(search_term)
        
        return instance
    
    def _init_search_spec(self, search_term: Union[str, List[str]]) -> None:
        """
        Initialize SearchSpec-specific attributes.
        This method handles the common initialization logic for both __init__ and _from_date_range.
        
        Args:
            search_term (Union[str, List[str]]): Search terms to process
        """
        # Load config
        self.config = load_config()
        
        # Check for false-like values
        if not search_term:
            raise ValueError("Search term argument search_term cannot be None or empty.")
        
        # Handle terms
        if isinstance(search_term, str):
            self.terms = [term.strip() for term in search_term.split(',')]
        else:
            self.terms = search_term
        
        # Check if the number of terms is greater than the max_terms parameter
        if len(self.terms) > self.config['api_parameters']['all']['max_terms']:
            raise ValueError(f"Number of search terms ({len(self.terms)}) exceeds the maximum allowed ({self.config['api_parameters']['all']['max_terms']})")
        
        self.term_string = ','.join(self.terms)

    def __str__(self):
        return f"{self.__class__.__name__} {self.term_string} {self.str.full_range_ymd}"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(search_term={self.term_string}, start_date={self.str.start_ymd}, end_date={self.str.end_ymd}, "
                f"granularity={self.granularity})")


    # @classmethod
    # def from_str(cls, date_str: str, granularity: str = 'D', range_space: str = ' ', verbose: bool = False) -> 'DateRange':
    #     """
    #     Create a DateRange instance from a date string.
        
    #     Args:
    #         date_str (str): Date range string in format like "Dec 31, 2023 - Jan 6, 2024" or "Jan 7 - 13, 2024"
    #         range_space (str): The string to use between dates in the output formattedrange. Defaults to a single space.
    #         granularity (str): The granularity of the date range. One of: 's' (seconds), 'm' (minutes), 'h' (hourly), 
    #                          'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'X' (decade).
    #                          Defaults to 'D'.
    #         verbose (bool): Whether to print verbose debug information. Defaults to False.
            
    #     Returns:
    #         DateRange: A new DateRange instance
            
    #     Raises:
    #         ValueError: If the date string cannot be parsed
    #     """
    #     dr = cls(granularity=granularity, range_space=range_space, verbose=verbose)
    #     dr._init_from_range_str(date_str, verbose)
    #     return dr

    # @classmethod
    # def from_dt(cls, dt: Union[datetime, List[datetime], Tuple[datetime, datetime]], granularity: str = 'D', range_space: str = ' ', verbose: bool = False) -> 'DateRange':
    #     """
    #     Create a new DateRange instance from a datetime object or a pair of datetime objects.
        
    #     Args:
    #         dt (Union[datetime, List[datetime], Tuple[datetime, datetime]]): Either a single datetime object
    #             or a list/tuple of two datetime objects
    #         range_space (str): The string to use between dates in the range. Defaults to a single space.
    #         granularity (str): The granularity of the date range. One of: 's' (seconds), 'm' (minutes), 'h' (hourly), 
    #                          'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'X' (decade).
    #                          Defaults to 'D'.
    #         verbose (bool): Whether to print verbose debug information. Defaults to False.
            
    #     Returns:
    #         DateRange: A new DateRange instance
            
    #     Raises:
    #         ValueError: If the input is not a datetime or a list/tuple of exactly two datetimes
    #     """
    #     dr = cls(granularity=granularity, range_space=range_space, verbose=verbose)
    #     dr._init_from_dt_pair(dt)
    #     return dr

    
    # def _init_from_dt_pair(self, dt: Union[datetime, List[datetime], Tuple[datetime, datetime]]) -> None:
    #     """
    #     Initialize this DateRange instance from a datetime object or a pair of datetime objects.
    #     This is a private method used by both __init__ and from_dt.
        
    #     Args:
    #         dt (Union[datetime, List[datetime], Tuple[datetime, datetime]]): Either a single datetime object
    #             or a list/tuple of two datetime objects
            
    #     Raises:
    #         ValueError: If the input is not a datetime or a list/tuple of exactly two datetimes
    #     """
    #     # Handle single datetime
    #     # if isinstance(dt, datetime):
    #     #     self.original_date_str = dt.isoformat()
    #     #     self.original_date_cleaned = _cleanup_date_str(self.original_date_str)
    #     #     dt = self._zero_time_if_needed(dt)
    #     #     self.start_dt = dt
    #     #     self.start_incomplete = False
    #     #     self.end_incomplete = True
    #     #     self._make_time_range(dt)
    #     #     return
            
    #     # Handle list/tuple of datetimes
    #     if isinstance(dt, (list, tuple)) and len(dt) == 2 and all(isinstance(d, datetime) for d in dt):
    #         start_dt, end_dt = dt
    #         self.original_date_str = f"{start_dt.isoformat()}{self.range_space}{end_dt.isoformat()}"
    #         self.original_date_cleaned = f"{cleanup_date_str(start_dt.isoformat())}{self.range_space}{cleanup_date_str(end_dt.isoformat())}"
    #         start_dt = self._zero_time_if_needed(start_dt)
    #         end_dt = self._zero_time_if_needed(end_dt)
    #         self.start_dt = start_dt
    #         self.end_dt = end_dt
    #         self.start_incomplete = False
    #         self.end_incomplete = False
            
    #         # Initialize granularity manager if not already done
    #         if not hasattr(self, 'granularity_manager'):
    #             self.granularity_manager = GranularityManager()
            
    #         # Use GranularityManager to format the time range
    #         time_range_data = self.granularity_manager.standardize_time_range(
    #             start=start_dt, 
    #             end=end_dt, 
    #             granularity=self.granularity,
    #             range_space=self.range_space
    #         )
            
    #         # Set the formatted attributes from the returned data
    #         self.start_dt = time_range_data["start_dt"]
    #         self.end_dt = time_range_data["end_dt"]
    #         self.formatted_start_ymd = time_range_data["formatted_start_ymd"]
    #         self.formatted_start_mdy = time_range_data["formatted_start_mdy"]
    #         self.formatted_end_ymd = time_range_data["formatted_end_ymd"]
    #         self.formatted_end_mdy = time_range_data["formatted_end_mdy"]
    #         self.formatted_range_ymd = time_range_data["formatted_range_ymd"]
    #         self.formatted_range_mdy = time_range_data["formatted_range_mdy"]
            
    #         return
            
    #     raise ValueError("DateRange Input must be a list/tuple of exactly two datetime objects")

        # if not (self.start_str and self.end_str):
        #     raise ValueError(f"Could not parse date string into start and end date: {clean_range_str}")
        # self.start_dt = parse_date_str(self.start_str)
        # self.end_dt = parse_date_str(self.end_str)
        # if self.start_dt >= self.end_dt:
        #     raise ValueError(f"End date must be after start date: {self.start_dt} >= {self.end_dt}")
        # self.start_incomplete = False
        # self.end_incomplete = False
        # return

        # # test for case like "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07"
        # if re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str):
        #     _print_if_verbose(f"Found ISO format date: {clean_date_str}", verbose)
        #     # extract the ISO format date
        #     self.start_date = re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str).group()
        #     self.start_dt = parse(self.start_date)
        #     # delete the first date from the string
        #     clean_date_str = clean_date_str.replace(self.start_date, '', 1).strip()
        #     # now see if there is another one
        #     if re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str):
        #         self.end_date = re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str).group()
        #         self.end_dt = parse(self.end_date)
        #         # delete the second date from the string
        #         clean_date_str = clean_date_str.replace(self.end_date, '', 1).strip()
        # # test for case like "11/3/2021 - 11/10/2021"
        # elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        #     _print_if_verbose(f"Found MM/DD/YYYY format date: {clean_date_str}", verbose)
        #     self.start_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        #     self.start_dt = parse(self.start_date)
        #     # delete the first date from the string
        #     clean_date_str = clean_date_str.replace(self.start_date, '', 1).strip()
        #     # now see if there is another one
        #     if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        #         self.end_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        #         self.end_dt = parse(self.end_date)
        #         # delete the second date from the string
        #         clean_date_str = re.split(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str)[1].strip()
        # # test for case like "Jan 1-7, 2020"
        # elif re.search(r'\d+-\d+', clean_date_str):
        #     _print_if_verbose(f"Found DD-DD format date: {clean_date_str}", verbose)
        #     parts = re.split(r'\d+-\d+', clean_date_str)
        #     splitter = re.search(r'\d+-\d+', clean_date_str).group()
        #     front_digits = re.search(r'\d+', splitter).group()
        #     back_digits = re.search(r'-\d+', splitter).group().lstrip('-')
        #     back_year = re.search(r'\d+$', parts[1]).group()
        #     self.start_date = parts[0] + front_digits + ', ' + back_year
        #     self.end_date = back_digits + parts[1]
        # # test for case like "Jan 1 - 7, 2020"
        # elif re.search(r'\d+\s*-\s*\d+', clean_date_str):
        #     _print_if_verbose(f"Found DD - DD format date: {clean_date_str}", verbose)
        #     parts = re.split(r'\d+\s*-\s*\d+', clean_date_str)
        #     splitter = re.search(r'\d+\s*-\s*\d+', clean_date_str).group()
        #     front_digits = re.search(r'\d+', splitter).group()
        #     back_digits = re.search(r'-\s*\d+', splitter).group().lstrip('-')
        #     back_year = re.search(r'\d+$', parts[1]).group()
        #     self.start_date = parts[0] + front_digits + ', ' + back_year
        #     self.end_date = back_digits + parts[1]
        # # test for case like "Jan 1-Dec 7, 2020"
        # elif re.search(r'\d+-[a-zA-Z]+', clean_date_str):
        #     _print_if_verbose(f"Found DD-MM format date: {clean_date_str}", verbose)
        #     parts = re.split(r'\d+-[a-zA-Z]+', clean_date_str)
        #     splitter = re.search(r'\d+-[a-zA-Z]+', clean_date_str).group()
        #     front_digits = re.search(r'\d+', splitter).group()
        #     back_letters = re.search(r'-[a-zA-Z]+', splitter).group().lstrip('-')
        #     back_year = re.search(r'\d+$', parts[1]).group()
        #     self.start_date = parts[0] + front_digits + ', ' + back_year
        #     self.end_date = back_letters + parts[1]
        # # search for case like "Jan 1 - Dec 7, 2020"
        # elif re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str):
        #     _print_if_verbose(f"Found DD - MM format date: {clean_date_str}", verbose)
        #     parts = re.split(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str)
        #     splitter = re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str).group()
        #     front_digits = re.search(r'\d+', splitter).group()
        #     back_letters = re.search(r'-\s*[a-zA-Z]+', splitter).group().lstrip('-').strip()
        #     back_year = re.search(r'\d+$', parts[1]).group()
        #     self.start_date = parts[0] + front_digits + ', ' + back_year
        #     self.end_date = back_letters + parts[1]
        # # if we get here we can assume there's only one date.
        # else:
        #     _print_if_verbose(f"Found single date: {clean_date_str}", verbose)
        #     try:
        #         self.start_date = clean_date_str
        #         self.start_dt = parse(clean_date_str)
        #     except (ValueError, ParserError) as e:
        #         _print_if_verbose(f"Could not parse date string: {clean_date_str}", verbose)
        #         raise ValueError(f"Could not parse date string: {clean_date_str}") from e

        # # Handle single date case
        # if self.start_date and not self.end_date:
        #     self.start_incomplete = False
        #     self.end_incomplete = True
        #     self.formatted_range_ymd = self.start_dt.strftime("%Y-%m-%d")
        #     self.formatted_range_mdy = self.start_dt.strftime("%m/%d/%Y")
        #     return

        # # Handle two dates case
        # if self.start_date:
        #     try:
        #         self.start_dt = parse(self.start_date)
        #         self.start_incomplete = False
        #     except (ParserError):
        #         pass
        # if self.end_date:
        #     try:
        #         self.end_dt = parse(self.end_date)
        #         self.end_incomplete = False
        #     except (ParserError):
        #         pass

        # # Handle incomplete dates
        # if self.start_incomplete and self.end_date:
        #     date_year = re.search(r'\d{4}\s*$', self.end_date).group()
        #     self.start_date = self.start_date + ', ' + date_year
        #     try:
        #         self.start_dt = parse(self.start_date)
        #         self.start_incomplete = False
        #     except (ParserError):
        #         pass

        # if self.end_incomplete and self.start_date:
        #     date_month = re.search(r'[a-zA-Z]{2,}', self.start_date).group()
        #     self.end_date = date_month + ' ' + self.end_date
        #     try:
        #         self.end_dt = parse(self.end_date)
        #         self.end_incomplete = False
        #     except (ParserError):
        #         pass

        # Note: Once we get to this point, we have both string and datetime objects for start date,
        # and, if provided, also for end date.
        # Now that we have parsed that out of the string, we make all the different representations
        # of the date or time range.
        # self._make_time_range(self.start_dt, self.end_dt)


    # def _zero_time_if_needed(self, dt_obj: datetime) -> datetime:
    #     """
    #     Helper method to zero out time components if needed based on granularity.
        
    #     Args:
    #         dt_obj (datetime): The datetime object to potentially zero out
            
    #     Returns:
    #         datetime: The datetime object with time components zeroed out if needed
    #     """
    #     if self.granularity not in ['h', 'm', 's']:
    #         return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    #     return dt_obj

    # def _make_time_range(
    #     self,
    #     start_date: datetime = None,
    #     end_date: datetime = None, 
    #     granularity: str = 'D'
    # ) -> 'DateRange':
    #     """
    #     Convert start_date and end_date into formatted time range strings and set instance attributes.
    #     If dates are strings, they will be parsed into datetime objects.
    #     Every instance of DateRange should use this method to properly set its date or time range attributes.
        
    #     Args:
    #         start_date (Optional[Union[str, datetime]]): Start date. If string, will be parsed with dateutil.parser
    #         end_date (Optional[Union[str, datetime]]): End date. If string, will be parsed with dateutil.parser
            
    #     Returns:
    #         DateRange: Returns self for method chaining
            
    #     Raises:
    #         ValueError: If neither start_date nor end_date is provided
    #         ValueError: If self.granularity is not one of: 's' (seconds), 'm' (minutes), 'h' (hourly), 
    #                    'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'X' (decade)
    #     """
    #     # Check if any dates are provided
    #     if not start_date or not end_date:
    #         raise ValueError("_make_time_range requires both start_date and end_date")

    #     # Parse string dates into datetime objects
    #     # Let's skip this for now because we're not using string dates anymore.
    #     # if isinstance(start_date, str):
    #     #     start_date = parse_date_str(start_date)
    #     # if isinstance(end_date, str):
    #     #     end_date = parse_date_str(end_date)
        
    #     # Truncate by provided granularity.
    #     if granularity == 's':
    #         # For seconds granularity:
    #         # - Both start and end dates are rounded down to the nearest second
    #         if start_date:
    #             start_date = start_date.replace(microsecond=0)
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%YT%H:%M:%S")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(microsecond=0)
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%YT%H:%M:%S")
    #             self.end_dt = end_date
    #     elif granularity == 'm':
    #         # For minutes granularity:
    #         # - Both start and end dates are rounded down to the nearest minute
    #         if start_date:
    #             start_date = start_date.replace(second=0, microsecond=0)
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%dT%H:%M")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%YT%H:%M")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(second=0, microsecond=0)
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%dT%H:%M")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%YT%H:%M")
    #             self.end_dt = end_date
    #     elif granularity == 'h':
    #         # For hourly granularity:
    #         # - Both start and end dates are rounded down to the nearest hour
    #         if start_date:
    #             start_date = start_date.replace(minute=0, second=0, microsecond=0)
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%dT%H")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%YT%H")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(minute=0, second=0, microsecond=0)
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%dT%H")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%YT%H")
    #             self.end_dt = end_date
    #     elif granularity == 'D':
    #         # For daily granularity:
    #         # - Both start and end dates are rounded down to the start of the day
    #         if start_date:
    #             start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     elif granularity == 'W':
    #         # For weekly granularity:
    #         # - Start date is truncated to previous Sunday (week start)
    #         # - End date is rounded up to next Saturday (week end)
    #         if start_date:
    #             start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    #             # Calculate days to subtract to get to previous Sunday (weekday 6)
    #             days_to_subtract = (start_date.weekday() + 1) % 7
    #             start_date = (start_date - timedelta(days=days_to_subtract)).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    #             # Calculate days to add to get to next Saturday (weekday 5)
    #             days_to_add = (5 - end_date.weekday()) % 7
    #             end_date = (end_date + timedelta(days=days_to_add)).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     elif granularity == 'M':
    #         # For monthly granularity:
    #         # - Start date is truncated to first day of the month
    #         # - End date is rounded to last day of the month
    #         if start_date:
    #             start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             # Get the first day of next month
    #             if end_date.month == 12:
    #                 next_month = end_date.replace(year=end_date.year + 1, month=1, day=1)
    #             else:
    #                 next_month = end_date.replace(month=end_date.month + 1, day=1)
    #             # Subtract one day to get last day of current month
    #             end_date = (next_month - timedelta(days=1)).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     elif granularity == 'Q':
    #         # For quarterly granularity:
    #         # - Start date is truncated to first day of the quarter (Jan 1, Apr 1, Jul 1, Oct 1)
    #         # - End date is rounded to last day of the quarter (Mar 31, Jun 30, Sep 30, Dec 31)
    #         if start_date:
    #             # Calculate the first month of the quarter (0-based)
    #             quarter_start_month = ((start_date.month - 1) // 3) * 3 + 1
    #             start_date = start_date.replace(
    #                 month=quarter_start_month,
    #                 day=1,
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             # Calculate the last month of the quarter (0-based)
    #             quarter_end_month = ((end_date.month - 1) // 3 + 1) * 3
    #             # Get the first day of next quarter
    #             if quarter_end_month == 12:
    #                 next_quarter = end_date.replace(year=end_date.year + 1, month=1, day=1)
    #             else:
    #                 next_quarter = end_date.replace(month=quarter_end_month + 1, day=1)
    #             # Subtract one day to get last day of current quarter
    #             end_date = (next_quarter - timedelta(days=1)).replace(
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     elif granularity == 'Y':
    #         # For yearly granularity:
    #         # - Start date is truncated to January 1st
    #         # - End date is rounded to December 31st
    #         if start_date:
    #             start_date = start_date.replace(
    #                 month=1,
    #                 day=1,
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             end_date = end_date.replace(
    #                 month=12,
    #                 day=31,
    #                 hour=0, minute=0, second=0, microsecond=0
    #             )
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     elif granularity == 'X':
    #         # For decade granularity:
    #         # - Start date is rounded down to the start of the decade (year ending in 0)
    #         # - End date is rounded to the end of the decade (last day of year ending in 9)
    #         if start_date:
    #             # Round down to start of decade
    #             decade_start = (start_date.year // 10) * 10
    #             start_date = start_date.replace(
    #                 year=decade_start,
    #                 month=1,
    #                 day=1,
    #                 hour=0,
    #                 minute=0,
    #                 second=0,
    #                 microsecond=0
    #             )
    #             self.formatted_start_ymd = start_date.strftime("%Y-%m-%d")
    #             self.formatted_start_mdy = start_date.strftime("%m/%d/%Y")
    #             self.start_dt = start_date
    #         if end_date:
    #             # Calculate first day of next decade
    #             next_decade = ((end_date.year // 10) + 1) * 10
    #             # Subtract one day to get last day of current decade
    #             end_date = (datetime(next_decade, 1, 1) - timedelta(days=1)).replace(
    #                 hour=0,
    #                 minute=0,
    #                 second=0,
    #                 microsecond=0
    #             )
    #             self.formatted_end_ymd = end_date.strftime("%Y-%m-%d")
    #             self.formatted_end_mdy = end_date.strftime("%m/%d/%Y")
    #             self.end_dt = end_date
    #     else:
    #         raise ValueError(f"Invalid granularity: {self.granularity}")

    #     # Create formatted range strings
    #     if start_date and end_date:
    #         self.formatted_range_ymd = f"{self.formatted_start_ymd}{self.range_space}{self.formatted_end_ymd}"
    #         self.formatted_range_mdy = f"{self.formatted_start_mdy}{self.range_space}{self.formatted_end_mdy}"
    #     else:
    #         raise ValueError("_make_time_range: start_date and end_date must be provided")
    #     # elif start_date:
    #     #     self.formatted_range_ymd = self.formatted_start_ymd
    #     #     self.formatted_range_mdy = self.formatted_start_mdy
    #     # elif end_date:
    #     #     self.formatted_range_ymd = self.formatted_end_ymd
    #     #     self.formatted_range_mdy = self.formatted_end_mdy

    #     return self


    # @property
    # def duration(self) -> timedelta:
    #     """
    #     Calculate the duration of the date range using period_index_full_duration.
        
    #     Returns:
    #         timedelta: The duration of the date range.
    #     """
    #     return period_index_full_duration(self.period_index)
    
    # @property
    # def periods(self) -> int:
    #     """
    #     Get the number of periods in the date range.
        
    #     Returns:
    #         int: The number of periods in the date range.
    #     """
    #     return len(self.period_index)


# def _cleanup_date_str(date_str: str) -> str:
#     """
#     Clean a date string. The unicode characters are converted to ascii and the unicode dashes are replaced with ascii dashes.
#     Cleanable unicode character values: \u2013\u2014\u2015\u2043\u2212\u23AF\u23E4\u2500\u2501\u2E3A\u2E3B\uFE58\uFE63\uFF0D
#     Cleanable unicode characters: – — ― ⁄ − ⎯ ⎴ ⎵ ⸺ ⸻ ﹘ ﹣ －
#     Args:
#         date_str (str): Date string to clean
        
#     Returns:
#         str: Cleaned date string
#     """
#     fixable_dashes_escaped = '\u2013\u2014\u2015\u2043\u2212\u23AF\u23E4\u2500\u2501\u2E3A\u2E3B\uFE58\uFE63\uFF0D'
#     fixable_dashes = '– — ― ⁄ − ⎯ ⎴ ⎵ ⸺ ⸻ ﹘ ﹣ －' # these are the ascii characters that are equivalent to the unicode characters. just here for reference.
#     fixable_nonprinting_escaped = '\u200B\u200C\u200D\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u202F\u2060\u2061\u2062\u2063\u2064\u2065\u2066\u2067\u2068\u2069\u206A\u206B\u206C\u206D\u206E\u206F\u20F0\u20F1\u20F2\u20F3\u20F4\u20F5\u20F6\u20F7\u20F8\u20F9\u20FA\u20FB\u20FC\u20FD\u20FE\u20FF'

#     date_str_unicode_normalized = unicodedata.normalize('NFKC', date_str).strip()
#     if not date_str_unicode_normalized.isascii():
#         for char in date_str_unicode_normalized:
#             if char.isascii():
#                 pass
#             elif char in fixable_dashes_escaped:
#                 _print_if_verbose(f"Swapping '-' for non-ascii character: {char} ({char.encode('unicode_escape').decode('ascii')})")
#             elif char in fixable_nonprinting_escaped:
#                 _print_if_verbose(f"Swapping non-printing character: {char.encode('unicode_escape').decode('ascii')}")
#     date_str_unicode_normalized = re.sub(f'[{fixable_dashes_escaped}]', '-', date_str_unicode_normalized)
#     date_str_unicode_normalized = re.sub(f'[{fixable_nonprinting_escaped}]', ' ', date_str_unicode_normalized)
#     date_str_unicode_normalized = re.sub(r'\s+', ' ', date_str_unicode_normalized)
#     date_str_unicode_normalized = date_str_unicode_normalized.strip()
#     return date_str_unicode_normalized


# def _split_date_range_str(clean_date_str: str) -> dict:
#     """
#     Parse a (possibly somewhat messy) date range string into a start and end date.
#     Args:
#         clean_date_str (str): The date string to parse. Must already be cleaned,
#         i.e. no messy unicode characters. (see _clean_date_str)
#     Returns:
#         str: The start and end date
#     """
#     start_date = None
#     end_date = None
#     #start_dt = None
#     #end_dt = None
#     #start_incomplete = False
#     #end_incomplete = False
    
#     # test for case like "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07"
#     if re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str):
#         #_print_if_verbose(f"Found ISO format date: {clean_date_str}", verbose)
#         # extract the ISO format date
#         start_date = re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str).group()
#         #start_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#         # delete the first date from the string
#         clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
#         # now see if there is another one
#         if re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str):
#             end_date = re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str).group()
#             #end_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             # delete the second date from the string
#             clean_date_str = clean_date_str.replace(end_date, '', 1).strip()
#     # test for case like "11/3/2021 - 11/10/2021"
#     elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
#         #_print_if_verbose(f"Found MM/DD/YYYY format date: {clean_date_str}", verbose)
#         start_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
#         #start_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#         # delete the first date from the string
#         clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
#         # now see if there is another one
#         if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
#             end_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
#             #end_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             # delete the second date from the string
#             clean_date_str = re.split(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str)[1].strip()
#     # test for case like "Jan 1-7, 2020"
#     elif re.search(r'\d+-\d+', clean_date_str):
#         #_print_if_verbose(f"Found DD-DD format date: {clean_date_str}", verbose)
#         parts = re.split(r'\d+-\d+', clean_date_str)
#         splitter = re.search(r'\d+-\d+', clean_date_str).group()
#         front_digits = re.search(r'\d+', splitter).group()
#         back_digits = re.search(r'-\d+', splitter).group().lstrip('-')
#         back_year = re.search(r'\d+$', parts[1]).group()
#         start_date = parts[0] + front_digits + ', ' + back_year
#         end_date = back_digits + parts[1]
#     # test for case like "Jan 1 - 7, 2020"
#     elif re.search(r'\d+\s*-\s*\d+', clean_date_str):
#         #_print_if_verbose(f"Found DD - DD format date: {clean_date_str}", verbose)
#         parts = re.split(r'\d+\s*-\s*\d+', clean_date_str)
#         splitter = re.search(r'\d+\s*-\s*\d+', clean_date_str).group()
#         front_digits = re.search(r'\d+', splitter).group()
#         back_digits = re.search(r'-\s*\d+', splitter).group().lstrip('-')
#         back_year = re.search(r'\d+$', parts[1]).group()
#         start_date = parts[0] + front_digits + ', ' + back_year
#         end_date = back_digits + parts[1]
#     # test for case like "Jan 1-Dec 7, 2020"
#     elif re.search(r'\d+-[a-zA-Z]+', clean_date_str):
#         #_print_if_verbose(f"Found DD-MM format date: {clean_date_str}", verbose)
#         parts = re.split(r'\d+-[a-zA-Z]+', clean_date_str)
#         splitter = re.search(r'\d+-[a-zA-Z]+', clean_date_str).group()
#         front_digits = re.search(r'\d+', splitter).group()
#         back_letters = re.search(r'-[a-zA-Z]+', splitter).group().lstrip('-')
#         back_year = re.search(r'\d+$', parts[1]).group()
#         start_date = parts[0] + front_digits + ', ' + back_year
#         end_date = back_letters + parts[1]
#     # search for case like "Jan 1 - Dec 7, 2020"
#     elif re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str):
#         #_print_if_verbose(f"Found DD - MM format date: {clean_date_str}", verbose)
#         parts = re.split(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str)
#         splitter = re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str).group()
#         front_digits = re.search(r'\d+', splitter).group()
#         back_letters = re.search(r'-\s*[a-zA-Z]+', splitter).group().lstrip('-').strip()
#         back_year = re.search(r'\d+$', parts[1]).group()
#         start_date = parts[0] + front_digits + ', ' + back_year
#         end_date = back_letters + parts[1]
#     else:
#         # if we get here we can assume there's only one date.
#         start_date = clean_date_str
#     return start_date, end_date



# def gtrend_standardize_date_range(start_date: datetime, end_date: datetime) -> dict:
#     """
#     Standardize a date range for Google Trends.
#     Args:
#         start_date (datetime): The start date
#         end_date (datetime): The end date
#     """



# def _parse_range_or_date_str(clean_date_str: str) -> dict:
#     """
#     Parse a (possibly somewhat messy) date range string into a start and end date.
#     Args:
#         clean_date_str (str): The date string to parse. Must already be cleaned,
#         i.e. no messy unicode characters. (see _clean_date_str)
#     Returns:
#         dict: A dictionary containing the start and end date, and the start and end date as datetime objects.
#     """
#     start_date, end_date = _split_date_range_str(clean_date_str)
#     if start_date and not end_date:
#         start_incomplete = False
#         end_incomplete = True
#         return {
#             'start_date': start_date,
#             'end_date': end_date,
#             'start_incomplete': start_incomplete,
#             'end_incomplete': end_incomplete,
#         }
#     else:
#         return {
#             'start_date': start_date,
#             'end_date': end_date,
#             'start_incomplete': start_incomplete,
#             'end_incomplete': end_incomplete,
#         }






#     # note to self!!!!! HERE I WANT TO CHANGE THIS TO ONLY PARSE THE STRINGS AND NOT DO DATETIME CONVERSION
#     else:
#         #_print_if_verbose(f"Found single date: {clean_date_str}", verbose)
#         try:
#             start_date = clean_date_str
#             start_dt = parse(clean_date_str, default=CURRENT_DEFAULT_DT)
#         except (ValueError, ParserError) as e:
#             #_print_if_verbose(f"Could not parse date string: {clean_date_str}", verbose)
#             raise ValueError(f"Could not parse date string: {clean_date_str}") from e

#     # Handle single date case
#     if start_date and not end_date:
#         start_incomplete = False
#         end_incomplete = True
#         #formatted_range_ymd = start_dt.strftime("%Y-%m-%d")
#         #formatted_range_mdy = start_dt.strftime("%m/%d/%Y")
#         return

#     # Handle two dates case
#     if start_date:
#         try:
#             start_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#             start_incomplete = False
#         except (ParserError):
#             pass
#     if end_date:
#         try:
#             end_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             end_incomplete = False
#         except (ParserError):
#             pass

#     # Handle incomplete dates
#     if start_incomplete and end_date:
#         date_year = re.search(r'\d{4}\s*$', end_date).group()
#         start_date = start_date + ', ' + date_year
#         try:
#             start_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#             start_incomplete = False
#         except (ParserError):
#             pass

#     if end_incomplete and start_date:
#         date_month = re.search(r'[a-zA-Z]{2,}', start_date).group()
#         end_date = date_month + ' ' + end_date
#         try:
#             end_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             end_incomplete = False
#         except (ParserError):
#             pass
    
#     components = {
#         'start_date': start_date,
#         'end_date': end_date,
#         'start_dt': start_dt,
#         'end_dt': end_dt,
#         'start_incomplete': start_incomplete,
#         'end_incomplete': end_incomplete,
#     }
#     return components

# def parse_range_or_date_str(date_str: str) -> dict:
#     """
#     Parse a (possibly somewhat messy) date range string into a start and end date.
#     As it is intended to be exposed to the user, it includes the unicode cleaning step.

#     Args:
#         date_str (str): The date string to parse.
#     Returns:
#         dict: A dictionary containing the start and end date, and the start and end date as datetime objects.
#     """
#     clean_date_str = _cleanup_date_str(date_str)
#     return _parse_range_or_date_str(clean_date_str)