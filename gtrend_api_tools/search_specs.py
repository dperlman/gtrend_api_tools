import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any, List, Tuple
from dateutil.parser import parse, ParserError
from gtrend_api_tools.utils import load_config, _print_if_verbose, period_index_full_duration
from gtrend_api_tools.utils import parse_date_str # parse_date_str is a wrapper for dateutil.parser.parse where we set the default the way we want it
from gtrend_api_tools.granularity import GranularityManager
import pandas as pd


class DateRange:
    """
    A class to handle date range operations and standardization.
    """
    def __init__(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        range_str: Optional[str] = None,
        granularity: str = 'D',
        range_space: str = ' ',
        verbose: bool = False
    ):
        self.original_date_str: Optional[str] = None
        self.original_date_cleaned: Optional[str] = None
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None
        self.start_date_dt: Optional[datetime] = None
        self.end_date_dt: Optional[datetime] = None
        self.start_incomplete: bool = True
        self.end_incomplete: bool = True
        self.formatted_range_ymd: Optional[str] = None
        self.formatted_range_mdy: Optional[str] = None
        self.granularity: str = granularity[0]  # Default to daily granularity, only use 1 character
        self.range_space: str = range_space

        # Initialize dates if provided
        # Note that if neither start_date nor end_date is provided, we leave those attributes as None.
        if range_str is not None:
            # Use range_str if provided
            self._init_from_range_str(range_str, verbose)
        elif (isinstance(start_date, (datetime, pd.Timestamp)) and 
              isinstance(end_date, (datetime, pd.Timestamp))):
            self._init_from_dt_pair([start_date, end_date])
        elif isinstance(start_date, str) and isinstance(end_date, str):
            self._init_from_range_str(f"{start_date} {end_date}", verbose)
        else:
            raise ValueError("Cannot initialize DateRange with given inputs. Please provide a range_str, or a start_date and end_date.")
        
        # we will keep an internal Pandas PeriodIndex object for reference.
        self.period_index = pd.period_range(start=self.start_date_dt, end=self.end_date_dt, freq=self.granularity)

        # fill out all the formatted output attributes
        self._make_time_range(self.start_date_dt, self.end_date_dt)


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

    
    def _init_from_dt_pair(self, dt: Union[datetime, List[datetime], Tuple[datetime, datetime]]) -> None:
        """
        Initialize this DateRange instance from a datetime object or a pair of datetime objects.
        This is a private method used by both __init__ and from_dt.
        
        Args:
            dt (Union[datetime, List[datetime], Tuple[datetime, datetime]]): Either a single datetime object
                or a list/tuple of two datetime objects
            
        Raises:
            ValueError: If the input is not a datetime or a list/tuple of exactly two datetimes
        """
        # Handle single datetime
        # if isinstance(dt, datetime):
        #     self.original_date_str = dt.isoformat()
        #     self.original_date_cleaned = _clean_date_str(self.original_date_str)
        #     dt = self._zero_time_if_needed(dt)
        #     self.start_date_dt = dt
        #     self.start_incomplete = False
        #     self.end_incomplete = True
        #     self._make_time_range(dt)
        #     return
            
        # Handle list/tuple of datetimes
        if isinstance(dt, (list, tuple)) and len(dt) == 2 and all(isinstance(d, datetime) for d in dt):
            start_date_dt, end_date_dt = dt
            self.original_date_str = f"{start_date_dt.isoformat()}{self.range_space}{end_date_dt.isoformat()}"
            self.original_date_cleaned = f"{_clean_date_str(start_date_dt.isoformat())}{self.range_space}{_clean_date_str(end_date_dt.isoformat())}"
            start_date_dt = self._zero_time_if_needed(start_date_dt)
            end_date_dt = self._zero_time_if_needed(end_date_dt)
            self.start_date_dt = start_date_dt
            self.end_date_dt = end_date_dt
            self.start_incomplete = False
            self.end_incomplete = False
            self._make_time_range(start_date_dt, end_date_dt)
            return
            
        raise ValueError("DateRange Input must be a list/tuple of exactly two datetime objects")


    def _init_from_range_str(self, date_str: str, verbose: bool = False) -> None:
        """
        Initialize this DateRange instance from a date string.
        This is a private method used by both __init__ and from_str.
        
        Args:
            date_str (str): Date range string in format like "Dec 31, 2023 - Jan 6, 2024" or "Jan 7 - 13, 2024"
            verbose (bool): Whether to print verbose debug information
            
        Raises:
            ValueError: If the date string cannot be parsed
        """
        # First clean the unicode to ascii because serpapi returns some weird unicode characters
        clean_date_str = _clean_date_str(date_str)
        self.original_date_str = date_str
        self.original_date_cleaned = clean_date_str
        # split the date range string into start and end date
        self.start_date, self.end_date = _split_date_range_str(clean_date_str)
        if not (self.start_date and self.end_date):
            raise ValueError(f"Could not parse date string into start and end date: {clean_date_str}")
        self.start_date_dt = parse_date_str(self.start_date)
        self.end_date_dt = parse_date_str(self.end_date)
        if self.start_date_dt >= self.end_date_dt:
            raise ValueError(f"End date must be after start date: {self.start_date_dt} >= {self.end_date_dt}")
        self.start_incomplete = False
        self.end_incomplete = False
        return

        # # test for case like "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07"
        # if re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str):
        #     _print_if_verbose(f"Found ISO format date: {clean_date_str}", verbose)
        #     # extract the ISO format date
        #     self.start_date = re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str).group()
        #     self.start_date_dt = parse(self.start_date)
        #     # delete the first date from the string
        #     clean_date_str = clean_date_str.replace(self.start_date, '', 1).strip()
        #     # now see if there is another one
        #     if re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str):
        #         self.end_date = re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str).group()
        #         self.end_date_dt = parse(self.end_date)
        #         # delete the second date from the string
        #         clean_date_str = clean_date_str.replace(self.end_date, '', 1).strip()
        # # test for case like "11/3/2021 - 11/10/2021"
        # elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        #     _print_if_verbose(f"Found MM/DD/YYYY format date: {clean_date_str}", verbose)
        #     self.start_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        #     self.start_date_dt = parse(self.start_date)
        #     # delete the first date from the string
        #     clean_date_str = clean_date_str.replace(self.start_date, '', 1).strip()
        #     # now see if there is another one
        #     if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        #         self.end_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        #         self.end_date_dt = parse(self.end_date)
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
        #         self.start_date_dt = parse(clean_date_str)
        #     except (ValueError, ParserError) as e:
        #         _print_if_verbose(f"Could not parse date string: {clean_date_str}", verbose)
        #         raise ValueError(f"Could not parse date string: {clean_date_str}") from e

        # # Handle single date case
        # if self.start_date and not self.end_date:
        #     self.start_incomplete = False
        #     self.end_incomplete = True
        #     self.formatted_range_ymd = self.start_date_dt.strftime("%Y-%m-%d")
        #     self.formatted_range_mdy = self.start_date_dt.strftime("%m/%d/%Y")
        #     return

        # # Handle two dates case
        # if self.start_date:
        #     try:
        #         self.start_date_dt = parse(self.start_date)
        #         self.start_incomplete = False
        #     except (ParserError):
        #         pass
        # if self.end_date:
        #     try:
        #         self.end_date_dt = parse(self.end_date)
        #         self.end_incomplete = False
        #     except (ParserError):
        #         pass

        # # Handle incomplete dates
        # if self.start_incomplete and self.end_date:
        #     date_year = re.search(r'\d{4}\s*$', self.end_date).group()
        #     self.start_date = self.start_date + ', ' + date_year
        #     try:
        #         self.start_date_dt = parse(self.start_date)
        #         self.start_incomplete = False
        #     except (ParserError):
        #         pass

        # if self.end_incomplete and self.start_date:
        #     date_month = re.search(r'[a-zA-Z]{2,}', self.start_date).group()
        #     self.end_date = date_month + ' ' + self.end_date
        #     try:
        #         self.end_date_dt = parse(self.end_date)
        #         self.end_incomplete = False
        #     except (ParserError):
        #         pass

        # Note: Once we get to this point, we have both string and datetime objects for start date,
        # and, if provided, also for end date.
        # Now that we have parsed that out of the string, we make all the different representations
        # of the date or time range.
        # self._make_time_range(self.start_date_dt, self.end_date_dt)


    def _zero_time_if_needed(self, dt_obj: datetime) -> datetime:
        """
        Helper method to zero out time components if needed based on granularity.
        
        Args:
            dt_obj (datetime): The datetime object to potentially zero out
            
        Returns:
            datetime: The datetime object with time components zeroed out if needed
        """
        if self.granularity not in ['h', 'm', 's']:
            return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        return dt_obj

    def _make_time_range(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None, 
    ) -> 'DateRange':
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
        if not start_date and not end_date:
            raise ValueError("At least one date must be provided")

        # Parse string dates into datetime objects
        if isinstance(start_date, str):
            start_date = parse_date_str(start_date)
        if isinstance(end_date, str):
            end_date = parse_date_str(end_date)
        
        # Truncate by provided granularity.
        if self.granularity == 's':
            # For seconds granularity:
            # - Both start and end dates are rounded down to the nearest second
            if start_date:
                start_date = start_date.replace(microsecond=0)
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%dT%H:%M:%S")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%YT%H:%M:%S")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(microsecond=0)
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%dT%H:%M:%S")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%YT%H:%M:%S")
                self.end_date_dt = end_date
        elif self.granularity == 'm':
            # For minutes granularity:
            # - Both start and end dates are rounded down to the nearest minute
            if start_date:
                start_date = start_date.replace(second=0, microsecond=0)
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%dT%H:%M")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%YT%H:%M")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(second=0, microsecond=0)
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%dT%H:%M")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%YT%H:%M")
                self.end_date_dt = end_date
        elif self.granularity == 'h':
            # For hourly granularity:
            # - Both start and end dates are rounded down to the nearest hour
            if start_date:
                start_date = start_date.replace(minute=0, second=0, microsecond=0)
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%dT%H")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%YT%H")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(minute=0, second=0, microsecond=0)
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%dT%H")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%YT%H")
                self.end_date_dt = end_date
        elif self.granularity == 'D':
            # For daily granularity:
            # - Both start and end dates are rounded down to the start of the day
            if start_date:
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        elif self.granularity == 'W':
            # For weekly granularity:
            # - Start date is truncated to previous Sunday (week start)
            # - End date is rounded up to next Saturday (week end)
            if start_date:
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                # Calculate days to subtract to get to previous Sunday (weekday 6)
                days_to_subtract = (start_date.weekday() + 1) % 7
                start_date = (start_date - timedelta(days=days_to_subtract)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                # Calculate days to add to get to next Saturday (weekday 5)
                days_to_add = (5 - end_date.weekday()) % 7
                end_date = (end_date + timedelta(days=days_to_add)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        elif self.granularity == 'M':
            # For monthly granularity:
            # - Start date is truncated to first day of the month
            # - End date is rounded to last day of the month
            if start_date:
                start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                # Get the first day of next month
                if end_date.month == 12:
                    next_month = end_date.replace(year=end_date.year + 1, month=1, day=1)
                else:
                    next_month = end_date.replace(month=end_date.month + 1, day=1)
                # Subtract one day to get last day of current month
                end_date = (next_month - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        elif self.granularity == 'Q':
            # For quarterly granularity:
            # - Start date is truncated to first day of the quarter (Jan 1, Apr 1, Jul 1, Oct 1)
            # - End date is rounded to last day of the quarter (Mar 31, Jun 30, Sep 30, Dec 31)
            if start_date:
                # Calculate the first month of the quarter (0-based)
                quarter_start_month = ((start_date.month - 1) // 3) * 3 + 1
                start_date = start_date.replace(
                    month=quarter_start_month,
                    day=1,
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                # Calculate the last month of the quarter (0-based)
                quarter_end_month = ((end_date.month - 1) // 3 + 1) * 3
                # Get the first day of next quarter
                if quarter_end_month == 12:
                    next_quarter = end_date.replace(year=end_date.year + 1, month=1, day=1)
                else:
                    next_quarter = end_date.replace(month=quarter_end_month + 1, day=1)
                # Subtract one day to get last day of current quarter
                end_date = (next_quarter - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        elif self.granularity == 'Y':
            # For yearly granularity:
            # - Start date is truncated to January 1st
            # - End date is rounded to December 31st
            if start_date:
                start_date = start_date.replace(
                    month=1,
                    day=1,
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                end_date = end_date.replace(
                    month=12,
                    day=31,
                    hour=0, minute=0, second=0, microsecond=0
                )
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        elif self.granularity == 'X':
            # For decade granularity:
            # - Start date is rounded down to the start of the decade (year ending in 0)
            # - End date is rounded to the end of the decade (last day of year ending in 9)
            if start_date:
                # Round down to start of decade
                decade_start = (start_date.year // 10) * 10
                start_date = start_date.replace(
                    year=decade_start,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                self.formatted_start_date_ymd = start_date.strftime("%Y-%m-%d")
                self.formatted_start_date_mdy = start_date.strftime("%m/%d/%Y")
                self.start_date_dt = start_date
            if end_date:
                # Calculate first day of next decade
                next_decade = ((end_date.year // 10) + 1) * 10
                # Subtract one day to get last day of current decade
                end_date = (datetime(next_decade, 1, 1) - timedelta(days=1)).replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                self.formatted_end_date_ymd = end_date.strftime("%Y-%m-%d")
                self.formatted_end_date_mdy = end_date.strftime("%m/%d/%Y")
                self.end_date_dt = end_date
        else:
            raise ValueError(f"Invalid granularity: {self.granularity}")

        # Create formatted range strings
        if start_date and end_date:
            self.formatted_range_ymd = f"{self.formatted_start_date_ymd}{self.range_space}{self.formatted_end_date_ymd}"
            self.formatted_range_mdy = f"{self.formatted_start_date_mdy}{self.range_space}{self.formatted_end_date_mdy}"
        elif start_date:
            self.formatted_range_ymd = self.formatted_start_date_ymd
            self.formatted_range_mdy = self.formatted_start_date_mdy
        elif end_date:
            self.formatted_range_ymd = self.formatted_end_date_ymd
            self.formatted_range_mdy = self.formatted_end_date_mdy

        return self

    
    def __str__(self):
        return f"DateRange {self.formatted_range_ymd}"
    
    def __repr__(self):
        return f"DateRange(start_date={self.start_date}, end_date={self.end_date}, granularity={self.granularity}, range_space='{self.range_space}')"
    
    @property
    def duration(self) -> timedelta:
        """
        Calculate the duration of the date range using period_index_full_duration.
        
        Returns:
            timedelta: The duration of the date range.
        """
        return period_index_full_duration(self.period_index)
    
    @property
    def periods(self) -> int:
        """
        Get the number of periods in the date range.
        
        Returns:
            int: The number of periods in the date range.
        """
        return len(self.period_index)


class GtrendDateRange(DateRange):
    """
    A class to handle date range operations and standardization for Google Trends.
    
    This class extends DateRange and automatically calculates the appropriate granularity
    based on the date range using the granularity rules from the configuration.
    
    Note: This class does not accept a granularity parameter. It always automatically
    calculates the appropriate granularity. If you need to specify granularity explicitly,
    use the DateRange base class instead.
    """
    def __init__(
        self,
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        range_str: Optional[str] = None,
        range_space: str = ' ',
        verbose: bool = False
    ):
        """
        Initialize a GtrendDateRange instance.
        
        This class automatically calculates the appropriate granularity based on the date range
        using the granularity rules from the configuration. If you need to specify a granularity
        explicitly, use the DateRange base class instead.
        
        Args:
            start_date (Optional[Union[str, datetime]]): Start date
            end_date (Optional[Union[str, datetime]]): End date
            range_str (Optional[str]): Date range string
            range_space (str): The string to use between dates in the output formatted range
            verbose (bool): Whether to print verbose debug information
        """
        # Load configuration and initialize granularity manager
        self.granularity_manager = GranularityManager() # will load config automatically
        
        # Calculate appropriate granularity using GranularityManager
        granularity_result = self.granularity_manager.calculate_search_granularity(
            start_date=start_date,
            end_date=end_date
        )
        
        calculated_granularity = granularity_result["granularity"]
        _print_if_verbose(f"Calculated granularity: {calculated_granularity}", verbose)
        
        # Initialize the parent DateRange class with the calculated granularity
        super().__init__(
            start_date=start_date,
            end_date=end_date,
            range_str=range_str,
            granularity=calculated_granularity,
            range_space=range_space,
            verbose=verbose
        )
        
        # Store additional granularity information
        self.granularity_info = granularity_result
    
    def get_granularity_info(self) -> Dict[str, Any]:
        """
        Get the granularity information that was calculated for this date range.
        
        Returns:
            Dict[str, Any]: Dictionary containing granularity information including:
                - granularity: The calculated granularity code
                - datetime_index: The DateTimeIndex for this range
                - period_index: The PeriodIndex for this range
                - max_units: Maximum units for this granularity
        """
        return self.granularity_info
    
    def get_max_units(self) -> Union[int, float]:
        """
        Get the maximum number of units allowed for the calculated granularity.
        
        Returns:
            Union[int, float]: Maximum units (inf for monthly)
        """
        return self.granularity_info.get("max_units", float('inf'))
    

    
    def __str__(self):
        return f"GtrendDateRange {self.formatted_range_ymd} (granularity: {self.granularity})"
    
    def __repr__(self):
        return f"GtrendDateRange(start_date={self.start_date}, end_date={self.end_date}, granularity={self.granularity}, calculated_granularity={self.granularity_info.get('granularity', 'N/A')})"



class SearchSpec(DateRange):
    """
    A class that extends DateRange to include search terms.
    This class handles both date range and search terms for a single search operation.
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
        # Load config
        self.config = load_config()
        
        # Check for false-like values
        if not search_term:
            raise ValueError("Search term argument search_termcannot be None or empty.")

        # Initialize DateRange - use provided date_range if available, otherwise pass kwargs to DateRange
        if date_range is not None and isinstance(date_range, DateRange):
            # Copy all attributes from the provided DateRange object
            super().__init__()
            self.__dict__.update(date_range.__dict__)
        else:
            # Filter out search_term from kwargs before passing to DateRange
            date_kwargs = {k: v for k, v in kwargs.items() if k != 'search_term'}
            # Pass filtered kwargs to DateRange constructor
            super().__init__(**date_kwargs)
        
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
        return f"SearchSpec {self.term_string} {self.formatted_range_ymd}"
    
    def __repr__(self):
        return f"SearchSpec(search_term={self.term_string}, start_date={self.start_date}, end_date={self.end_date}, granularity={self.granularity})"
    

def _clean_date_str(date_str: str) -> str:
    """
    Clean a date string. The unicode characters are converted to ascii and the unicode dashes are replaced with ascii dashes.
    Cleanable unicode character values: \u2013\u2014\u2015\u2043\u2212\u23AF\u23E4\u2500\u2501\u2E3A\u2E3B\uFE58\uFE63\uFF0D
    Cleanable unicode characters: – — ― ⁄ − ⎯ ⎴ ⎵ ⸺ ⸻ ﹘ ﹣ －
    Args:
        date_str (str): Date string to clean
        
    Returns:
        str: Cleaned date string
    """
    fixable_dashes_escaped = '\u2013\u2014\u2015\u2043\u2212\u23AF\u23E4\u2500\u2501\u2E3A\u2E3B\uFE58\uFE63\uFF0D'
    fixable_dashes = '– — ― ⁄ − ⎯ ⎴ ⎵ ⸺ ⸻ ﹘ ﹣ －' # these are the ascii characters that are equivalent to the unicode characters. just here for reference.
    fixable_nonprinting_escaped = '\u200B\u200C\u200D\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u202F\u2060\u2061\u2062\u2063\u2064\u2065\u2066\u2067\u2068\u2069\u206A\u206B\u206C\u206D\u206E\u206F\u20F0\u20F1\u20F2\u20F3\u20F4\u20F5\u20F6\u20F7\u20F8\u20F9\u20FA\u20FB\u20FC\u20FD\u20FE\u20FF'

    date_str_unicode_normalized = unicodedata.normalize('NFKC', date_str).strip()
    if not date_str_unicode_normalized.isascii():
        for char in date_str_unicode_normalized:
            if char.isascii():
                pass
            elif char in fixable_dashes_escaped:
                _print_if_verbose(f"Swapping '-' for non-ascii character: {char} ({char.encode('unicode_escape').decode('ascii')})")
            elif char in fixable_nonprinting_escaped:
                _print_if_verbose(f"Swapping non-printing character: {char.encode('unicode_escape').decode('ascii')}")
    date_str_unicode_normalized = re.sub(f'[{fixable_dashes_escaped}]', '-', date_str_unicode_normalized)
    date_str_unicode_normalized = re.sub(f'[{fixable_nonprinting_escaped}]', ' ', date_str_unicode_normalized)
    date_str_unicode_normalized = re.sub(r'\s+', ' ', date_str_unicode_normalized)
    date_str_unicode_normalized = date_str_unicode_normalized.strip()
    return date_str_unicode_normalized


def _split_date_range_str(clean_date_str: str) -> dict:
    """
    Parse a (possibly somewhat messy) date range string into a start and end date.
    Args:
        clean_date_str (str): The date string to parse. Must already be cleaned,
        i.e. no messy unicode characters. (see _clean_date_str)
    Returns:
        str: The start and end date
    """
    start_date = None
    end_date = None
    #start_date_dt = None
    #end_date_dt = None
    #start_incomplete = False
    #end_incomplete = False
    
    # test for case like "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07"
    if re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str):
        #_print_if_verbose(f"Found ISO format date: {clean_date_str}", verbose)
        # extract the ISO format date
        start_date = re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str).group()
        #start_date_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
        # delete the first date from the string
        clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
        # now see if there is another one
        if re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str):
            end_date = re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str).group()
            #end_date_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
            # delete the second date from the string
            clean_date_str = clean_date_str.replace(end_date, '', 1).strip()
    # test for case like "11/3/2021 - 11/10/2021"
    elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        #_print_if_verbose(f"Found MM/DD/YYYY format date: {clean_date_str}", verbose)
        start_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        #start_date_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
        # delete the first date from the string
        clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
        # now see if there is another one
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
            end_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
            #end_date_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
            # delete the second date from the string
            clean_date_str = re.split(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str)[1].strip()
    # test for case like "Jan 1-7, 2020"
    elif re.search(r'\d+-\d+', clean_date_str):
        #_print_if_verbose(f"Found DD-DD format date: {clean_date_str}", verbose)
        parts = re.split(r'\d+-\d+', clean_date_str)
        splitter = re.search(r'\d+-\d+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_digits = re.search(r'-\d+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_digits + parts[1]
    # test for case like "Jan 1 - 7, 2020"
    elif re.search(r'\d+\s*-\s*\d+', clean_date_str):
        #_print_if_verbose(f"Found DD - DD format date: {clean_date_str}", verbose)
        parts = re.split(r'\d+\s*-\s*\d+', clean_date_str)
        splitter = re.search(r'\d+\s*-\s*\d+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_digits = re.search(r'-\s*\d+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_digits + parts[1]
    # test for case like "Jan 1-Dec 7, 2020"
    elif re.search(r'\d+-[a-zA-Z]+', clean_date_str):
        #_print_if_verbose(f"Found DD-MM format date: {clean_date_str}", verbose)
        parts = re.split(r'\d+-[a-zA-Z]+', clean_date_str)
        splitter = re.search(r'\d+-[a-zA-Z]+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_letters = re.search(r'-[a-zA-Z]+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_letters + parts[1]
    # search for case like "Jan 1 - Dec 7, 2020"
    elif re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str):
        #_print_if_verbose(f"Found DD - MM format date: {clean_date_str}", verbose)
        parts = re.split(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str)
        splitter = re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_letters = re.search(r'-\s*[a-zA-Z]+', splitter).group().lstrip('-').strip()
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_letters + parts[1]
    else:
        # if we get here we can assume there's only one date.
        start_date = clean_date_str
    return start_date, end_date



def gtrend_standardize_date_range(start_date: datetime, end_date: datetime) -> dict:
    """
    Standardize a date range for Google Trends.
    Args:
        start_date (datetime): The start date
        end_date (datetime): The end date
    """



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
#             start_date_dt = parse(clean_date_str, default=CURRENT_DEFAULT_DT)
#         except (ValueError, ParserError) as e:
#             #_print_if_verbose(f"Could not parse date string: {clean_date_str}", verbose)
#             raise ValueError(f"Could not parse date string: {clean_date_str}") from e

#     # Handle single date case
#     if start_date and not end_date:
#         start_incomplete = False
#         end_incomplete = True
#         #formatted_range_ymd = start_date_dt.strftime("%Y-%m-%d")
#         #formatted_range_mdy = start_date_dt.strftime("%m/%d/%Y")
#         return

#     # Handle two dates case
#     if start_date:
#         try:
#             start_date_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#             start_incomplete = False
#         except (ParserError):
#             pass
#     if end_date:
#         try:
#             end_date_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             end_incomplete = False
#         except (ParserError):
#             pass

#     # Handle incomplete dates
#     if start_incomplete and end_date:
#         date_year = re.search(r'\d{4}\s*$', end_date).group()
#         start_date = start_date + ', ' + date_year
#         try:
#             start_date_dt = parse(start_date, default=CURRENT_DEFAULT_DT)
#             start_incomplete = False
#         except (ParserError):
#             pass

#     if end_incomplete and start_date:
#         date_month = re.search(r'[a-zA-Z]{2,}', start_date).group()
#         end_date = date_month + ' ' + end_date
#         try:
#             end_date_dt = parse(end_date, default=CURRENT_DEFAULT_DT)
#             end_incomplete = False
#         except (ParserError):
#             pass
    
#     components = {
#         'start_date': start_date,
#         'end_date': end_date,
#         'start_date_dt': start_date_dt,
#         'end_date_dt': end_date_dt,
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
#     clean_date_str = _clean_date_str(date_str)
#     return _parse_range_or_date_str(clean_date_str)