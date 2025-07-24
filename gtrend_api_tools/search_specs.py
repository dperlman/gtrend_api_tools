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
from gtrend_api_tools.APIs.api_utils import available_apis
from gtrend_api_tools.date_strings import parse_date_str, split_date_range_str, cleanup_date_str, get_resolution_details # parse_date_str is a wrapper for dateutil.parser.parse where we set the default the way we want it
from gtrend_api_tools.granularity import GranularityManager
import pandas as pd
from types import SimpleNamespace
from gtrend_api_tools.date_strings import CURRENT_DEFAULT_DT



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
        periods: Optional[int] = None,
        freq: Optional[str] = None,
        resolution: Optional[str] = 'h',
        range_space: str = ' ',
        verbose: bool = False
    ):
        self.original_start: Optional[str] = start
        self.original_end: Optional[str] = end
        self.original_range_str: Optional[str] = range_str
        self.periods: Optional[int] = periods
        self.freq: Optional[str] = freq
        self.resolution: str = resolution
        self.range_space: str = range_space
        self.verbose: bool = verbose
        self.original_start_str: Optional[str] = None
        self.original_end_str: Optional[str] = None
        self.original_start_dt: Optional[datetime] = None
        self.original_end_dt: Optional[datetime] = None
        self.start_dt: datetime
        self.last_index_dt: datetime
        self.end_dt: datetime
        self.period_index: pd.PeriodIndex
        self.num_periods: int
        self.duration: timedelta
        self.str: SimpleNamespace = SimpleNamespace()

        # First we need to sort out range_str, start, and end.
        self._init_range_str_start_end(range_str, start, end, periods, freq)

        # Now we have good self.original_start_dt and self.original_end_dt.
        # Now set up the internal detailed parameters we need
        self._init_date_range_info()

        # Get the resolution arguments and apply them to the start and end dates and range strings
        self._apply_resolution()

    # Private methods

    def _init_range_str_start_end(
        self,
        range_str: Optional[str],
        start: Optional[Union[str, datetime]],
        end: Optional[Union[str, datetime]],
        periods: Optional[int],
        freq: Optional[str]
    ) -> None:
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

        # Now we either have start_date and end_date from range_str,
        # or if range_str was not provided, we have whatever was given for start, end, periods, and freq.
        # We need 3 of the 4 of start, end, periods, and freq to be set before we can initialize the date range info.
        # Check for this condition and raise an error if it's not met.
        # provided = [start is not None, end is not None, periods is not None, freq is not None]
        # if sum(provided) < 3:
        #     raise ValueError("DateRange requires at least 3 of the 4 parameters: start, end, periods, freq to be set (start and end may be provided in range_str).")

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
        elif start is not None:
            parse_errors += f"invalid start: {start} "

        if isinstance(end, str):
            self.original_end_str = end
            self.original_end_dt = parse_date_str(end)
            if self.original_end_dt is None:
                parse_errors += f"invalid end: {end} "
        elif isinstance(end, (datetime, pd.Timestamp)):
            self.original_end_dt = end
        elif end is not None:
            parse_errors += f"invalid end: {end}"

        if parse_errors:
            raise ValueError(f"Cannot initialize DateRange with given inputs: {parse_errors}")

        # Once we get here, we have set original_start_dt and original_end_dt.
        # Original_start_str and original_end_str are set only if `start` and `end` were strings.
        # One last sanity check: we don't want to allow start_dt to be greater than end_dt
        # And while we're at it, let's just arbitrarily set the minimum to one second
        # But Only validate start/end relationship if both are provided
        if self.original_start_dt is not None and self.original_end_dt is not None:
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
        self.period_index = pd.period_range(start=self.original_start_dt, end=self.original_end_dt, freq=self.freq, periods=self.periods)
        self.datetime_index = self.period_index.to_timestamp().tz_localize(CURRENT_DEFAULT_DT.tzinfo)
        # print(self.datetime_index.freqstr)
        self.extended_period_index = self.period_index.union([self.period_index[-1] + 1])
        self.extended_datetime_index = self.extended_period_index.to_timestamp().tz_localize(CURRENT_DEFAULT_DT.tzinfo)

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

        # Now make lists of date strings based on the datetime_index
        self.datetime_str_list_ymd = [dt.replace(**res_args).strftime(format_str_ymd) for dt in self.datetime_index]
        self.datetime_str_list_mdy = [dt.replace(**res_args).strftime(format_str_mdy) for dt in self.datetime_index]


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
    def __init__(self,
                 *args,
                 api: Optional[str] = None,
                 granularity_manager: Optional[GranularityManager] = None,
                 **kwargs):
        # Just make sure we are not receiving the arguments `granularity` or `freq` or `resolution`.
        if 'granularity' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `granularity`")
        if 'freq' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `freq`")
        if 'resolution' in kwargs:
            raise ValueError(f"{self.__class__.__name__} does not accept the argument `resolution`")
        if 'start' not in kwargs or kwargs['start'] is None:
            raise ValueError(f"{self.__class__.__name__} requires the argument `start`")
        if 'end' not in kwargs or kwargs['end'] is None:
            raise ValueError(f"{self.__class__.__name__} requires the argument `end`")
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
        self.api = api
        self.granularity_manager = granularity_manager

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
        if self.granularity_manager is None:
            self.granularity_manager = GranularityManager(api=self.api) # will load config automatically
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
        self.str.search_start_ymd = self.original_start_dt.strftime(format_str_ymd)
        self.str.search_start_mdy = self.original_start_dt.strftime(format_str_mdy)
        self.str.search_end_ymd = self.original_end_dt.strftime(format_str_ymd)
        self.str.search_end_mdy = self.original_end_dt.strftime(format_str_mdy)
        # These are the new properties we have, beyond the base class properties
        self.str.search_range_ymd = f"{self.str.search_start_ymd}{self.range_space}{self.str.search_end_ymd}"
        self.str.search_range_mdy = f"{self.str.search_start_mdy}{self.range_space}{self.str.search_end_mdy}"

    def __str__(self):
        return f"{self.__class__.__name__} {self.str.full_range_ymd} (granularity: {self.granularity})"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(start_date={self.str.start_ymd}, end_date={self.str.end_ymd}, "
                f"granularity={self.granularity}), freq={self.freq}, resolution={self.resolution}, search_resolution={self.search_resolution}")


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
            # # Filter out search_term from kwargs before passing to DateRange
            # date_kwargs = {k: v for k, v in kwargs.items() if k != 'search_term'}
            # # Pass filtered kwargs to DateRange constructor
            # super().__init__(**date_kwargs)
            super().__init__(**kwargs)
            
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

        # Initialize api if provided
        instance.api = kwargs['api'] if 'api' in kwargs else None
        
        return instance
    
    def _init_search_spec(self, search_term: Union[str, List[str]]) -> None:
        """
        Initialize SearchSpec-specific attributes.
        This method handles the common initialization logic for both __init__ and _from_date_range.
        
        Args:
            search_term (Union[str, List[str]]): Search terms to process
            api (Optional[str]): The API to use. This is only useful for batch processing.
        """
        # Load config
        self.config = load_config()
        # Check if api is provided and validate it against allowed APIs in config
        _print_if_verbose(f"SearchSpec(api={self.api}) initializing search spec")
        if self.api is not None and self.api not in available_apis:
            raise ValueError(f"API '{self.api}' is not allowed. Allowed APIs are: {available_apis.keys()}")
        
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
        return f"{self.__class__.__name__} {self.term_string} {self.str.index_range_ymd}"
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(search_term={self.term_string}, range_str={self.str.index_range_ymd}, "
                f"granularity={self.granularity})")


########################################################
# CompoundSearchSpec class. 
########################################################

class CompoundSearchSpec(SearchSpec):
    """
    A class that extends SearchSpec to handle compound search operations.
    This class is a placeholder for future compound search functionality.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Implement compound search functionality
        pass