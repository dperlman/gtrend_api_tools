import re
from datetime import datetime, timezone
from dateutil.parser import parse

# default datetime object for parser is january 1 of current year and has hour zero
CURRENT_DEFAULT_DT = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

def parse_date_str(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object using the CURRENT_DEFAULT_DT as the default.
    """
    try:
        parsed_date = parse(date_str, default=CURRENT_DEFAULT_DT)
    except ValueError:
        #print(f"Error parsing date string: {date_str} trying again with dateparser.parse")
        import dateparser
        tz = CURRENT_DEFAULT_DT.strftime('%Z')
        parsed_date = dateparser.parse(date_str, settings={'TIMEZONE': tz})
    return parsed_date

def standardize_date_time_str(date_time_str: str) -> str:
    """
    Standardize a date time string to a YYYY-MM-DDTHH:MM:SS format.
    """
    clean_date_time_str = cleanup_date_str(date_time_str)
    #print(f"clean_date_time_str: {clean_date_time_str}")
    parsed_date = parse_date_str(clean_date_time_str)
    #print(f"parsed_date: {parsed_date}")
    return parsed_date.strftime("%Y-%m-%dT%H:%M:%S")

def split_date_range_str(date_str: str) -> tuple:
    """
    Parse a (possibly somewhat messy) date range string into a start and end date.
    Args:
        date_str (str): The date string to parse. Will be cleaned,
        i.e. removing messy unicode characters. (see cleanup_date_str)
    Returns:
        tuple: The start and end date as strings
    """
    clean_date_str = cleanup_date_str(date_str)

    # test for cases like
    #  Dec 31, 2017 - Jan 6, 2018
    #  Dec 29, 2019 - Jan 4, 2020
    # with zero or more spaces around the - or single space
    mdy_date_match = re.search(
        r'^(\w+\s+\d{1,2}[, ]+\d{4})\s*[- ]\s*(\w+\s+\d{1,2}[, ]+\d{4})',
        clean_date_str
    )
    if mdy_date_match:
        start_date, end_date = mdy_date_match.groups()
        return start_date, end_date

    # test for cases like
    #  2020-01-01T14:30:45 2020-01-07T14:30:45
    #  2020-01-01T14:30 2020-01-07T14:30
    #  2020-01-01T14 2020-01-07T14
    # or
    #  2020-01-01T14:30:45 - 2020-01-07T14:30:45
    #  2020-01-01T14:30 - 2020-01-07T14:30
    #  2020-01-01T14 - 2020-01-07T14
    # with zero or more spaces around the - or single space
    iso_datetime_match = re.search(
        r'^(\d{4}-\d{2}-\d{2}T\d{2}(?::\d{2}(?::\d{2})?)?)\s*[- ]\s*(\d{4}-\d{2}-\d{2}T\d{2}(?::\d{2}(?::\d{2})?)?)$',
        clean_date_str
    )
    if iso_datetime_match:
        start_date, end_date = iso_datetime_match.groups()
        return start_date, end_date

    # test for cases like
    #  01/01/2020T14:30:45 01/07/2020T14:30:45
    #  01/01/2020T14:30 01/07/2020T14:30
    #  01/01/2020T14 01/07/2020T14
    # or
    #  01/01/2020T14:30:45 - 01/07/2020T14:30:45
    #  01/01/2020T14:30 - 01/07/2020T14:30
    #  01/01/2020T14 - 01/07/2020T14
    # with zero or more spaces around the - or single space
    mdy_datetime_match = re.search(
        r'^(\d{1,2}/\d{1,2}/\d{4}T\d{2}(?::\d{2}(?::\d{2})?)?)\s*[- ]\s*(\d{1,2}/\d{1,2}/\d{4}T\d{2}(?::\d{2}(?::\d{2})?)?)',
        clean_date_str
    )
    if mdy_datetime_match:
        start_date, end_date = mdy_datetime_match.groups()
        return start_date, end_date

    # test for cases like
    #  2020-01-01 - 2020-01-07
    #  2020-01-01 2020-01-07
    # with zero or more spaces around the - or single space
    iso_date_match = re.search(
        r'^(\d{4}-\d{2}-\d{2})\s*[- ]\s*(\d{4}-\d{2}-\d{2})',
        clean_date_str
    )
    if iso_date_match:
        start_date, end_date = iso_date_match.groups()
        return start_date, end_date
    
    # test for cases like
    #  11/3/2021 - 11/10/2021
    #  11/3/2021 11/10/2021
    # with zero or more spaces around the - or single space
    mdy_date_match = re.search(
        r'^(\d{1,2}/\d{1,2}/\d{2,4})\s*[- ]\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        clean_date_str
    )
    if mdy_date_match:
        start_date, end_date = mdy_date_match.groups()
        return start_date, end_date
    
    # test for cases like
    # 12/31/23, 5:00 PM - 1/6/24, 5:00 PM
    # and also with seconds, e.g., 12/31/23, 5:00:45 PM - 1/6/24, 5:00:45 PM
    # with zero or more spaces around the - or single space
    mdy_date_match = re.search(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm])\s*[- ]\s*(\d{1,2}/\d{1,2}/\d{2,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm])',
        clean_date_str
    )

    if mdy_date_match:  
        start_date, end_date = mdy_date_match.groups()
        return start_date, end_date

    # test for cases like
    # 2023-12-31, 5:00 PM - 2024-1-6, 5:00 PM
    # and also with seconds, e.g., "2023-12-31, 5:00:45 PM - 2024-1-6, 5:00:45 PM"
    # with zero or more spaces around the - or single space
    iso_mdy_time_match = re.search(
        r'^(\d{4}-\d{1,2}-\d{1,2}[, ]+\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm])\s*[- ]\s*(\d{4}-\d{1,2}-\d{1,2}[, ]+\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm])',
        clean_date_str
    )
    if iso_mdy_time_match:
        start_date, end_date = iso_mdy_time_match.groups()
        return start_date, end_date
    
    # test for 24-hour time cases like
    # 12/31/23, 5:00 - 1/6/24, 5:00
    # and also with seconds, e.g., 12/31/23, 5:00:45 - 1/6/24, 5:00:45
    # with zero or more spaces around the - or single space
    mdy_24h_time_match = re.search(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?)\s*[- ]\s*(\d{1,2}/\d{1,2}/\d{2,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?)',
        clean_date_str
    )

    if mdy_24h_time_match:  
        start_date, end_date = mdy_24h_time_match.groups()
        return start_date, end_date

    # test for 24-hour time cases like
    # 2023-12-31, 5:00 - 2024-1-6, 5:00
    # and also with seconds, e.g., "2023-12-31, 5:00:45 - 2024-1-6, 5:00:45"
    # with zero or more spaces around the - or single space
    iso_24h_time_match = re.search(
        r'^(\d{4}-\d{1,2}-\d{1,2}[, ]+\d{1,2}:\d{2}(?::\d{2})?)\s*[- ]\s*(\d{4}-\d{1,2}-\d{1,2}[, ]+\d{1,2}:\d{2}(?::\d{2})?)',
        clean_date_str
    )
    if iso_24h_time_match:
        start_date, end_date = iso_24h_time_match.groups()
        return start_date, end_date

    # # test for cases like
    # #  Jan 1-7, 2020
    # #  Jan 1-7 2020
    # # with no spaces around the "-"
    # if re.search(r'\w+\s+\d+-\d+,?\s+\d+', clean_date_str):
    #     parts        = re.split (r'\d+-\d+', clean_date_str)
    #     splitter     = re.search(r'\d+-\d+', clean_date_str).group()
    #     front_digits = re.search(r'\d+', splitter).group()
    #     back_digits  = re.search(r'-\d+', splitter).group().lstrip('-')
    #     front_month  = re.search(r'\w+', parts[0]).group()
    #     back_year    = re.search(r'\d+$', parts[1]).group()
    #     start_date = front_month + ' ' + front_digits + ', ' + back_year
    #     end_date = front_month + ' ' + back_digits + ', ' + back_year
    #     return start_date, end_date

    # test for cases like
    #  Jan 1 - 7, 2020
    #  Jan 1 - 7 2020
    #  Jan 1  -  7, 2020
    # with zero or more spaces around the "-"
    if re.search(r'^\w+\s+\d+\s*-\s*\d+[, ]+\d+', clean_date_str):
        parts        = re.split (r'\d+\s*-\s*\d+', clean_date_str)
        splitter     = re.search(r'\d+\s*-\s*\d+', clean_date_str).group()
        front_day    = re.search(r'\d+', splitter).group()
        back_day     = re.search(r'-\s*\d+', splitter).group().lstrip('-').strip()
        front_month  = re.search(r'\w+', parts[0]).group()
        back_year    = re.search(r'\d+$', parts[1]).group()
        start_date = front_month + ' ' + front_day + ', ' + back_year
        end_date = front_month + ' ' + back_day + ', ' + back_year
        return start_date, end_date

    # # test for cases like
    # #  Jan 1-Dec 7, 2020
    # #  Jan 1-Dec 7 2020
    # # with no spaces around the "-"
    # if re.search(r'\d+-[a-zA-Z]+', clean_date_str):
    #     parts = re.split(r'\d+-[a-zA-Z]+', clean_date_str)
    #     splitter = re.search(r'\d+-[a-zA-Z]+', clean_date_str).group()
    #     front_digits = re.search(r'\d+', splitter).group()
    #     back_letters = re.search(r'-[a-zA-Z]+', splitter).group().lstrip('-')
    #     back_year = re.search(r'\d+$', parts[1]).group()
    #     start_date = parts[0] + front_digits + ', ' + back_year
    #     end_date = parts[0] + back_letters + back_year
    #     return start_date, end_date
    
    # search for cases like
    #  Jan 1 - Dec 7, 2020
    #  Jan 1 - Dec 7 2020
    #  Jan 1  -  Dec 7, 2020
    # with one or more spaces around the "-"
    if re.search(r'^\w+\s+\d+\s*-\s*\w+\s+\d+[, ]+\d+', clean_date_str):
        parts        = re.split (r'\d+\s*-\s*\w+', clean_date_str)
        splitter     = re.search(r'\d+\s*-\s*\w+', clean_date_str).group()
        front_month  = re.search(r'^\w+', parts[0]).group()
        front_day    = re.search(r'\d+', splitter).group()
        back_month   = re.search(r'-\s*\w+', splitter).group().lstrip('-').strip()
        back_day     = re.search(r'\d+', parts[1]).group()
        back_year    = re.search(r'\d+$', parts[1]).group()
        start_date = front_month + ' ' + front_day + ', ' + back_year
        end_date = back_month + ' ' + back_day + ', ' + back_year
        return start_date, end_date
    
    # if we get here we can assume there's only one date.
    start_date = clean_date_str
    end_date = None
    return start_date, end_date 

def standardize_date_format(date_str: str) -> str:
    """
    Standardize the date format to YYYY-MM-DD.
    """
    cleaned_date_str = cleanup_date_str(date_str)
    date_dt = parse_date_str(cleaned_date_str)
    return date_dt.strftime("%Y-%m-%dT%H:%M:%S")

def standardize_date_range_start(date_str: str) -> str:
    """
    Get the start date from a date range string.
    """
    start_date_str = split_date_range_str(cleanup_date_str(date_str))[0]
    return standardize_date_format(start_date_str)

def standardize_date_index(date_list: list) -> list:
    """
    Standardize a list of date strings.
    Used in every API's standardize_data method because I updated date string
    parsing once and it broke everything. This way I can change the logic of how our standardize_data method works
    in one central place.
    """
    standard_date_list = [None] * len(date_list)
    for i, date in enumerate(date_list):
        standard_date_list[i] = standardize_date_range_start(date)
    return standard_date_list

def cleanup_date_str(date_str: str) -> str:
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

    import unicodedata
    import re
    date_str_unicode_normalized = unicodedata.normalize('NFKC', date_str).strip()
    # The following debug print is omitted for modularity
    date_str_unicode_normalized = re.sub(f'[{fixable_dashes_escaped}]', '-', date_str_unicode_normalized)
    date_str_unicode_normalized = re.sub(f'[{fixable_nonprinting_escaped}]', ' ', date_str_unicode_normalized)
    date_str_unicode_normalized = re.sub(r'\s+', ' ', date_str_unicode_normalized)
    date_str_unicode_normalized = date_str_unicode_normalized.strip()
    return date_str_unicode_normalized 

def get_resolution_details(resolution: str) -> tuple:
    """
    Get the resolution arguments from a frequency string.
    The format strings are meant to be used to format date strings,
    while the resolution arguments are meant to be used to replace the values in a datetime object.
    This is used in the DateRange class to get the resolution arguments and format strings for the output date range.
    
    Args:
        resolution (str): The resolution string.
    Returns:
        tuple: (dict: The resolution arguments,
                str: The format string for YYYY-MM-DD,
                str: The format string for MM/DD/YYYY)
    """
    res_args = {}
    if resolution == 's':
        res_args['microsecond'] = 0
        format_str_ymd = '%Y-%m-%dT%H:%M:%S'
        format_str_mdy = '%m/%d/%YT%H:%M:%S'
    if resolution == 'm':
        res_args['second'] = 0
        res_args['microsecond'] = 0
        format_str_ymd = '%Y-%m-%dT%H:%M'
        format_str_mdy = '%m/%d/%YT%H:%M'
    if resolution == 'h':
        res_args['minute'] = 0
        res_args['second'] = 0
        res_args['microsecond'] = 0
        format_str_ymd = '%Y-%m-%dT%H'
        format_str_mdy = '%m/%d/%YT%H'
    if resolution == 'D':
        res_args['hour'] = 0
        res_args['minute'] = 0
        res_args['second'] = 0
        res_args['microsecond'] = 0
        format_str_ymd = '%Y-%m-%d'
        format_str_mdy = '%m/%d/%Y'
    if resolution == 'M':
        res_args['day'] = 1
        res_args['hour'] = 0
        res_args['minute'] = 0
        res_args['second'] = 0
        res_args['microsecond'] = 0
        format_str_ymd = '%Y-%m'
        format_str_mdy = '%m/%Y'
    if resolution == 'Y':
        res_args['month'] = 1
        res_args['day'] = 1
        res_args['hour'] = 0
        res_args['minute'] = 0
        res_args['second'] = 0
        res_args['microsecond'] = 0
        format_str_ymd = '%Y'
        format_str_mdy = '%Y'
    return res_args, format_str_ymd, format_str_mdy