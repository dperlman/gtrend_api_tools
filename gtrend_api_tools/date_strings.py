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
        print(f"Error parsing date string: {date_str} trying again with dateparser.parse")
        import dateparser
        tz = CURRENT_DEFAULT_DT.strftime('%Z')
        parsed_date = dateparser.parse(date_str, settings={'TIMEZONE': tz})
    return parsed_date


def split_date_range_str(clean_date_str: str) -> tuple:
    """
    Parse a (possibly somewhat messy) date range string into a start and end date.
    Args:
        clean_date_str (str): The date string to parse. Must already be cleaned,
        i.e. no messy unicode characters. (see clean_date_str)
    Returns:
        tuple: The start and end date as strings
    """
    start_date = None
    end_date = None
    
    # test for case like "2020-01-01 - 2020-01-07 or 2020-01-01 2020-01-07"
    if re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str):
        # extract the ISO format date
        start_date = re.search(r'^\d{4}-\d{2}-\d{2}', clean_date_str).group()
        # delete the first date from the string
        clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
        # now see if there is another one
        if re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str):
            end_date = re.search(r'\d{4}-\d{2}-\d{2}', clean_date_str).group()
            # delete the second date from the string
            clean_date_str = clean_date_str.replace(end_date, '', 1).strip()
    # test for case like "11/3/2021 - 11/10/2021"
    elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
        start_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
        # delete the first date from the string
        clean_date_str = clean_date_str.replace(start_date, '', 1).strip()
        # now see if there is another one
        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str):
            end_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str).group()
            # delete the second date from the string
            clean_date_str = re.split(r'\d{1,2}/\d{1,2}/\d{4}', clean_date_str)[1].strip()
    # test for case like "Jan 1-7, 2020"
    elif re.search(r'\d+-\d+', clean_date_str):
        parts = re.split(r'\d+-\d+', clean_date_str)
        splitter = re.search(r'\d+-\d+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_digits = re.search(r'-\d+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_digits + parts[1]
    # test for case like "Jan 1 - 7, 2020"
    elif re.search(r'\d+\s*-\s*\d+', clean_date_str):
        parts = re.split(r'\d+\s*-\s*\d+', clean_date_str)
        splitter = re.search(r'\d+\s*-\s*\d+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_digits = re.search(r'-\s*\d+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_digits + parts[1]
    # test for case like "Jan 1-Dec 7, 2020"
    elif re.search(r'\d+-[a-zA-Z]+', clean_date_str):
        parts = re.split(r'\d+-[a-zA-Z]+', clean_date_str)
        splitter = re.search(r'\d+-[a-zA-Z]+', clean_date_str).group()
        front_digits = re.search(r'\d+', splitter).group()
        back_letters = re.search(r'-[a-zA-Z]+', splitter).group().lstrip('-')
        back_year = re.search(r'\d+$', parts[1]).group()
        start_date = parts[0] + front_digits + ', ' + back_year
        end_date = back_letters + parts[1]
    # search for case like "Jan 1 - Dec 7, 2020"
    elif re.search(r'\d+\s*-\s*[a-zA-Z]+', clean_date_str):
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

def standardize_date_format(date_str: str) -> str:
    """
    Standardize the date format to YYYY-MM-DD.
    """
    cleaned_date_str = cleanup_date_str(date_str)
    date_dt = parse_date_str(cleaned_date_str)
    return date_dt.strftime("%Y-%m-%d")

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