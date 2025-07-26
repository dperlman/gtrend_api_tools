import applescript
from urllib.parse import quote
from datetime import datetime, timedelta
import time
import sys
from typing import Optional, Callable, List, Dict, Any, Union, Literal
import rjsmin
import html
from bs4 import BeautifulSoup
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchResult, TrendSearchInternalState
import pandas as pd
from gtrend_api_tools.utils import _print_if_verbose
from gtrend_api_tools.search_specs import DateRange, GtrendDateRange
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start
import json
import unicodedata


class AuthenticationError(Exception):
    """Raised when Google authentication fails."""
    pass

class JavaScriptError(Exception):
    """Raised when JavaScript execution fails."""
    pass

# Global search terms by name
CONFIRM_CONFIGS = {
    'google_auth_choose': {
        'url': 'https://accounts.google.com/AccountChooser',
        'auth_email': 'omgoleus@gmail.com',
        'auth_email_queryselector': 'div[data-email]',
        'terms': [
            {'term': 'Choose an account', 'queryselector': 'html body h1 span[jsslot]'}
        ]
    },
    'google_auth': {
        'url': 'https://accounts.google.com/AccountChooser',
        'terms': [
            {'term': 'Welcome', 'queryselector': 'html body h1'},
            {'term': 'Personal info', 'queryselector': 'html body nav ul'},
            {'term': 'Data & privacy', 'queryselector': 'html body nav ul'},
        ]
    },
    'google_trends': {
        'url': 'https://trends.google.com/trends/explore?date={date_range}&geo={geo}&q={query}&hl=en',
        'terms': [
            {'term': 'Interest over time', 'queryselector': 'div.fe-line-chart-header-title'},
            {'term': 'Trending Now', 'queryselector': 'a.tab-title'},
            {'term': 'x1', 'queryselector': 'div.line-chart-body-wrapper bar-chart div.bar-chart-content div div div div table'},
            {'term': 'x', 'queryselector': 'div.line-chart-body-wrapper line-chart-directive div div div div div table'}
        ]
    }
}

PARSE_CONFIGS = {
    'date_range': {
        'string_to_search_for': '-',
        'queryselector': 'custom-date-picker md-select md-select-value span div._md-text'
    },
    'data_table': {
        'string_to_search_for': 'y1',
        'queryselector': 'div.line-chart-body-wrapper line-chart-directive div div div div div table'
    }
}

class GoogleAuthSession:
    def __init__(
        self,
        safari_instance: 'ApplescriptSafari',
        poll_max_tries: int = 3,
        poll_wait_time: int = 1,
        print_func: Optional[Callable] = None,
        auth_email: Optional[str] = None
    ):
        """
        Initialize a Google Authentication Session.
        
        Args:
            safari_instance (ApplescriptSafari): The parent ApplescriptSafari instance
            poll_max_tries (int): Maximum number of attempts to find the text
            poll_wait_time (int): Time to wait between attempts in seconds
            print_func (Optional[Callable]): Function to use for printing debug information
            auth_email (Optional[str]): Email to use for Google authentication
        """
        self.safari = safari_instance
        self.poll_max_tries = poll_max_tries
        self.poll_wait_time = poll_wait_time
        self.print_func = print_func or _print_if_verbose
        self.auth_email = auth_email
        self._auth_status = None

    def login(self) -> 'GoogleAuthSession':
        """
        Perform Google authentication and store the result.
        
        Returns:
            GoogleAuthSession: Returns self for method chaining
            
        Raises:
            AuthenticationError: If any step of the authentication process fails
        """
        # Get the Google auth configs
        account_chooser_config = CONFIRM_CONFIGS['google_auth_choose']
        auth_config = CONFIRM_CONFIGS['google_auth']
        
        self.print_func("Checking Google authentication...")
        self.print_func(f"URL: {account_chooser_config['url']}")
        
        # Open the URL
        self.safari.open_url_in_safari(account_chooser_config['url'])
        
        # Check for the Account Chooser page
        elements = self.safari.poll_for_text(
            search_texts=[term['term'] for term in account_chooser_config['terms']],
            query_selectors=[term['queryselector'] for term in account_chooser_config['terms']]
        )
        if not elements:
            self._auth_status = 'unconfirmed'
            raise AuthenticationError("Failed to find Account Chooser page")
        
        # Check for auth_email
        self.print_func(f"\nChecking for email: {account_chooser_config['auth_email']}")
        elements = self.safari.poll_for_text(
            search_texts=account_chooser_config['auth_email'],
            query_selectors=account_chooser_config['auth_email_queryselector'],
            click=True
        )
        if not elements:
            self._auth_status = 'unconfirmed'
            raise AuthenticationError("Failed to find and click email address")

        # Check for initial term (Welcome)
        initial_term = auth_config['terms'][0]
        self.print_func(f"\nChecking for '{initial_term['term']}' text...")
        
        # Try to find the initial term
        elements = self.safari.poll_for_text(
            search_texts=initial_term['term'],
            query_selectors=initial_term['queryselector']
        )
        if not elements:
            self._auth_status = 'unconfirmed'
            raise AuthenticationError("Failed to find Welcome page after email selection")
        
        # Check for confirmation texts (all terms)
        elements = self.safari.poll_for_text(
            search_texts=[term['term'] for term in auth_config['terms'][1:]],
            query_selectors=[term['queryselector'] for term in auth_config['terms'][1:]]
        )
        if not elements:
            self._auth_status = 'unconfirmed'
            raise AuthenticationError("Failed to find additional confirmation navigation elements")
            
        self._auth_status = 'confirmed'
        return self

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the session is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._auth_status == 'confirmed'

    @property
    def auth_status(self) -> Optional[Literal['confirmed', 'unconfirmed']]:
        """
        Get the current authentication status.
        
        Returns:
            Optional[Literal['confirmed', 'unconfirmed']]: The current authentication status
        """
        return self._auth_status

class ApplescriptSafari(API_Call):
    def __init__(
        self,
        auth_email: Optional[str] = CONFIRM_CONFIGS['google_auth_choose']['auth_email'],
        close_tabs: bool = False,
        poll_max_tries: int = 3,
        poll_wait_time: int = 1,
        api_endpoint: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the ApplescriptSafari class.
        
        Args:
            auth_email (Optional[str]): Email address to use for Google authentication. If None, no specific email will be used.
            close_tabs (bool): If True, close the first Safari tab before each search. Defaults to False.
            poll_max_tries (int): Maximum number of attempts to find text. Defaults to 3.
            poll_wait_time (int): Time to wait between attempts in seconds. Defaults to 1.
            api_endpoint (Optional[str]): The API endpoint URL. Must be None for this class because we aren't calling an endpoint.
            **kwargs: Additional keyword arguments passed to API_Call
        """
        if api_endpoint is not None:
            raise ValueError("api_endpoint must be None for this class because we aren't calling an endpoint.")
        super().__init__(api_endpoint=api_endpoint, **kwargs)
        self._window_created = False
        self.auth_email = auth_email
        self._auth_session = None
        self.close_tabs = close_tabs
        self.poll_max_tries = poll_max_tries
        self.poll_wait_time = poll_wait_time


    # def search(self, **kwargs) -> 'ApplescriptSafari':
    #     """
    #     Search Google Trends using AppleScript and Safari.
        
    #     Args:
    #         **kwargs: Arguments passed to the parent class search method
            
    #     Returns:
    #         ApplescriptSafari: Returns self for method chaining
    #     """
    #     # Set up search parameters using base class logic
    #     internal_state = self._setup_search(**kwargs)
    #     # Initialize history with the internal state
    #     self._initialize_history([internal_state])


    def _do_search(self, internal_state: TrendSearchInternalState) -> 'ApplescriptSafari':
        # Get the processed search spec for dates
        spec = internal_state.search_spec
        
        # Create auth session if it doesn't exist
        if self._auth_session is None:
            self.print_func("Creating new GoogleAuthSession")
            self._auth_session = GoogleAuthSession(
                safari_instance=self,
                print_func=self.print_func,
                auth_email=self.auth_email
            )
        
        # Check Google authentication
        if not self._auth_session.is_authenticated:
            self._auth_session.login()
        if not self._auth_session.is_authenticated:
            raise Exception("Google authentication login failed")

        self.print_func(f"Sending ApplescriptSafari search request:")
        self.print_func(f"  Search term: {spec.term_string}")
        self.print_func(f"  Search date range: {spec.str.search_range_ymd}")
        
        # Use the base trends URL from internal_state instead of constructing our own
        formatted_url = internal_state.base_trends_request_url
        self.print_func(f"Opening URL: {formatted_url}")
        
        # Open URL in Safari, creating window only if needed
        self.open_url_in_safari(formatted_url)
        
        # Get the raw HTML from the trends page
        # NOTE!!!! We also need to get the date range from the search part of the returned page.
        # custom-date-picker md-select md-select-value span div._md-text text value of this element.
        raw_data = self.parse_trends_page(spec.terms[0])
        if not raw_data:
            raise Exception("Failed to parse trends page")

        internal_state.search_result.raw_data = raw_data
        
        self.print_func("Search successful!")
        
        # Close tab if configured to do so
        if self.close_tabs:
            self.print_func("Closing front Safari tab")
            self._close_front_safari_tab()

        return self

    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert ApplescriptSafari raw data to standardized format.
        Parses the HTML table into a list of dictionaries with date and values.
        
        Args:
            raw_data (Any): Raw data from ApplescriptSafari (contains HTML and date range)
            
        Returns:
            Any: Standardized data in the common format
            
        Raises:
            ValueError: If raw data doesn't contain expected structure
        """
        # # Get the date range from the raw data
        # date_range_str = raw_data['date_range_text']
        # self.print_func(f"Raw date range: {date_range_str}")
        
        # # Parse it into a date range object
        # date_range = DateRange(range_str=date_range_str, freq=self.internal_state.search_spec.freq, resolution=self.internal_state.search_spec.search_resolution)
        # self.print_func(f"Parsed date range with DateRange: {repr(date_range)}")

        # # Parse the terms HTML using BeautifulSoup
        # soup = BeautifulSoup(raw_data['terms_html'], 'html.parser')
        # terms = [th.text.strip() for th in soup.find_all('th')]
        # self.print_func(f"Trends page terms table headers: {terms}")
        # # strip the first element of the list
        # search_terms = terms[1:]
        # self.print_func(f"Trends page search terms: {search_terms}")

        # Get the search terms from the page title
        search_terms = raw_data['page_title_text'].split(' - ')[0].split(',')
        search_terms = [term.strip() for term in search_terms]
        self.print_func(f"Trends page search terms: {search_terms}")

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(raw_data['trends_html'], 'html.parser')
        
        # Find the table
        table = soup.find('table')
        if not table:
            raise ValueError("No table found in HTML data")
            
        # Get headers (column names)
        headers = [th.text.strip() for th in table.find_all('th')]
        if not headers:
            raise ValueError("No headers found in table")
            
        # The first column should be 'x' (dates)
        if headers[0] != 'x':
            raise ValueError("First column is not 'x' (dates)")
            
        # Get all rows
        tbody = table.find('tbody')
        rows = tbody.find_all('tr')
        # Sanity check that the number of rows is the same as the number of dates in the date range
        #if len(rows) != len(date_range.datetime_str_list_ymd):
        #    raise ValueError(f"Number of rows in table ({len(rows)}) does not match number of dates in date range ({len(date_range.datetime_str_list_ymd)})")
        
        # Get search terms from search_spec
        # search_terms = self.internal_state.search_spec.terms
        # if not isinstance(search_terms, list):
        #     search_terms = [search_terms]
        
        # Transform the data into the standardized format
        raw_date_list = []
        data = []
        for i, row in enumerate(rows):
            cells = row.find_all('td')
            if len(cells) != len(headers):
                continue  # Skip malformed rows
                
            # Parse the date
            date_str = cells[0].text.strip()
            raw_date_list.append(date_str)
            standardized_date_str = standardize_date_range_start(date_str)
            #raw_date_list.append(date_range.datetime_str_list_ymd[i])
                
            # Get values for each column (except the date column)
            values = []
            for j, cell in enumerate(cells[1:], 1):
                try:
                    value = int(cell.text.strip())
                    # Use the search term from search_spec
                    search_term = search_terms[j-1] if j-1 < len(search_terms) else f"term_{j}"
                    values.append({
                        'value': value,
                        'query': search_term
                    })
                except ValueError:
                    continue  # Skip invalid values
                    
            if values:  # Only add entries that have valid values
                standardized_entry = {
                    #'date': date_range.datetime_str_list_ymd[i],
                    'date': standardized_date_str,
                    'values': values
                }
                data.append(standardized_entry)
        
        if not data:
            raise ValueError("No valid data found in table")
            
        self.print_func(f"Standardized data length: {len(data)}")
        return data

    # def standardize_data(self) -> 'ApplescriptSafari':
    #     """
    #     Standardize the raw HTML data into a common format.
    #     This method is kept for backward compatibility but now uses the TrendSearchResult system.
        
    #     Returns:
    #         ApplescriptSafari: Returns self for method chaining
    #     """
    #     # The standardization now happens automatically through the TrendSearchResult system
    #     # This method is kept for backward compatibility but doesn't need to do anything
    #     return self


    def parse_trends_page(self, search_terms: Union[str, List[str]]) -> Dict[str, str]:
        """
        Parse the Google Trends page using poll_for_text to check for expected elements.
        Uses a predefined set of terms to verify the page has loaded correctly.
        
        Args:
            search_terms (Union[str, List[str]]): The search term(s) being used
            
        Returns:
            Dict[str, str]: Dictionary containing 'terms_html', 'date_range_text', and 'trends_html'
        """
        # This may need to be changed if Google changes the Trends page, which they often do, to stop us from doing exactly this.
        # Get the trends config
        trends_config = CONFIRM_CONFIGS['google_trends']
        date_range_config = PARSE_CONFIGS['date_range']
        data_table_config = PARSE_CONFIGS['data_table']
            
        # Get the number of search terms
        num_terms = len(search_terms) if isinstance(search_terms, list) else 1
        # Limit to maximum of 5 terms
        num_terms = min(num_terms, 5)
        
        # Base terms that should always be present
        self.print_func("Checking for expected elements on trends page...")
        
        # Check all terms from config in one call
        elements = self.poll_for_text(
            search_texts=[term['term'] for term in trends_config['terms']],
            query_selectors=[term['queryselector'] for term in trends_config['terms']]
        )
        # Initialize raw_data dictionary now, because we need to return it even if we don't find all the elements.
        raw_data = {
            'date_range_text': '',
            'page_title_text': '',
            'meta_description_text': '',
            'terms_table_html': '',
            'trends_html': ''
        }
        
        if not elements:
            self.print_func("Warning: Expected elements were not found on the page")
            return raw_data # empty raw_data dictionary
        
        
        # Get the date range text
        self.print_func("Getting date range html...")
        date_range_element = self.get_element_by_text(
            date_range_config['string_to_search_for'],
            query_selector=date_range_config['queryselector'],
            get_container_table=False
        )
        self.print_func(f"Raw date_range_element: {date_range_element}")
        # Check if date_range_element has a 'text' attribute and if the text attribute is non-empty
        if date_range_element and 'text' in date_range_element[0] and date_range_element[0]['text']:
            self.print_func(f"Trends page date range: {date_range_element[0]['text']}")
            raw_data['date_range_text'] = date_range_element[0]['text']
        else:
            self.print_func("Could not find date range element text")

        # Get the y1 element outerHTML because that's the actual trends data we want.
        self.print_func("Getting y1 element container table...")
        y1_elements = self.get_element_by_text(
            search_text=trends_config['terms'][-1]['term'],
            query_selector=trends_config['terms'][-1]['queryselector'],
            get_container_table=True
        )
        if y1_elements[0]['containerTable']:
            self.print_func("Found y1 element container table.")
            container_table  = y1_elements[0]['containerTable']
            # Prettify the HTML using BeautifulSoup
            soup = BeautifulSoup(container_table, 'html.parser')
            prettified_html = soup.prettify()
            # self.print_func(f"Trends page trends: {prettified_html}")
            raw_data['trends_html'] = prettified_html
        else:
            self.print_func("Could not find y1 element container table")
            # self.print_func(f"y1_elements: {y1_elements}")


        # We want to get the list of search terms. There are a few ways to try to scrape this.
        # Can get it from the page title.
        self.print_func("Getting search terms from page title...")
        page_title_text = self.get_element_by_text(
            search_text='',
            query_selector='title',
            get_container_table=False
        )
        self.print_func(f"Raw page_title_text: {page_title_text}")
        # Check if date_range_element has a 'text' attribute and if the text attribute is non-empty
        if page_title_text and 'text' in page_title_text[0] and page_title_text[0]['text']:
            self.print_func(f"Trends page title text: {page_title_text[0]['text']}")
            raw_data['page_title_text'] = page_title_text[0]['text']
        else:
            self.print_func("Could not find page title text")
        
        # The table of search terms header only seems to show up if there are multiple search terms.
        # So we won't use this one after all.
        # self.print_func("Getting table of search terms...")
        # terms_elements = self.get_element_by_text(
        #     search_text=trends_config['terms'][-2]['term'],
        #     query_selector=trends_config['terms'][-2]['queryselector'],
        #     get_container_table=True
        # )
        # if terms_elements[0]['containerTable']:
        #     self.print_func("Found terms element container table.")
        #     container_table  = terms_elements[0]['containerTable']
        #     # Prettify the HTML using BeautifulSoup
        #     soup = BeautifulSoup(container_table, 'html.parser')            
        #     prettified_html = soup.prettify()
        #     # self.print_func(f"Trends page terms: {prettified_html}")
        #     raw_data['terms_table_html'] = prettified_html
        # else:
        #     self.print_func("Could not find terms element container table")
        #     # self.print_func(f"terms_elements: {terms_elements}")


        return raw_data


    def open_url_in_safari(self, url: str, load_delay: int = 0) -> None:
        """
        Open a URL in the current Safari window using AppleScript.
        Always uses the front window and creates a new tab.
        
        Args:
            url (str): The URL to open
            load_delay (int): Number of seconds to wait after opening URL for page to load. Default is 0 seconds.
        """
        try:
            self.print_func(f"Preparing to open URL: {url}")
            # AppleScript to open URL in new tab of front window, with fallback to open location
            script = f'''
            tell application "Safari"
                activate
                try
                    tell window 1
                        set current tab to make new tab with properties {{URL:"{url}"}}
                    end tell
                on error
                    open location "{url}"
                end try
            end tell
            '''
            self.print_func("Executing AppleScript...")
            
            # Run the AppleScript
            result = applescript.run(script)
            
            if result.code == 0:
                self.print_func(f"Successfully opened URL: {url}")
                # Add a delay to ensure the page loads
                self.print_func(f"Waiting {load_delay} seconds for page to load...")
                time.sleep(load_delay)
            else:
                self.print_func(f"Error opening URL: {result.err}")
                self.print_func(f"Error code: {result.code}")
                
        except Exception as e:
            self.print_func(f"Error executing AppleScript: {str(e)}")
            self.print_func(f"Error type: {type(e)}")
            raise

    def get_element_by_text(self, search_text: str, query_selector: Optional[str] = None, click: bool = False, get_container_table: bool = False) -> List[Dict[str, str]]:
        """
        Get elements containing the given text using JavaScript.
        
        Args:
            search_text (str): The text to search for
            query_selector (Optional[str]): CSS query selector to narrow down the search
            click (bool): If True, clicks the first matching element. Defaults to False.
            get_container_table (bool): If True, includes container table information in results. Defaults to False.
        Returns:
            List[Dict[str, str]]: List of dictionaries containing tag and text for each matching element.
            Only returns elements with matchType 'text' or 'script'. Returns empty list if only debug data found.
        """
        self.print_func(f"get_element_by_text: get_container_table: {get_container_table}")

        # Get the JavaScript code
        escaped_js = get_escaped_js_for_text_search_v3(search_text, query_selector or "*", self.print_func, click=click, get_container_table=get_container_table)
        
        # AppleScript to execute JavaScript
        script = f'''
        tell application "Safari"
            do JavaScript "{escaped_js}" in current tab of front window
        end tell
        '''
        for attempt in range(1, self.poll_max_tries + 1):
            self.print_func(f"get_element_by_text: attempt {attempt} of {self.poll_max_tries}")
            # Run the AppleScript
            self.print_func("get_element_by_text: about to run AppleScript")
            result = applescript.run(script)
            self.print_func(f"get_element_by_text: finished applescript:")
            self.print_func(f"get_element_by_text: result.code: {result.code}")
            self.print_func(f"get_element_by_text: result.err: {result.err}")
            
            data = None
            if result.code == 0:
                # Parse the JSON response
                try:
                    response = result.out
                    data = json.loads(response)
                    if isinstance(data, list):
                        # This is the case where we found the elements
                        self.print_func(f"get_element_by_text: Found {len(data)} elements.")
                        for element in data:
                            self.print_func(f"get_element_by_text: {element['domPath']}")
                        return data
                    elif isinstance(data, dict):
                        # This is the case where we received debug from the JavaScript
                        self.print_func(f"get_element_by_text: Error or Debug response.")
                    else:
                        self.print_func(f"get_element_by_text: Unexpected response: {data}")
                except json.JSONDecodeError as e:
                    self.print_func(f"get_element_by_text: Error parsing JSON response: {str(e)}")
                    self.print_func(f"get_element_by_text: Response: {response}")
            else:
                self.print_func(f"get_element_by_text: Error executing JavaScript: {result.err}")
            self.print_func(f"get_element_by_text: Trying again after {self.poll_wait_time} seconds...")
            time.sleep(self.poll_wait_time)
            
        # This is the case where we received debug from the JavaScript
        if not data:
            # This is the case where we received an error from the JavaScript
            self.print_func("get_element_by_text: No data found")
            raise
        elif data.get('matchType') == 'debug':
            # self.print_func("Debug response:")
            # self.print_func(f"  Element count: {data.get('elementCount')}")
            # self.print_func(f"  Search text: {data.get('searchText')}")
            # self.print_func(f"  Document ready: {data.get('documentReady')}")
            # self.print_func(f"  URL: {data.get('url')}")
            # self.print_func(f"  Title: {data.get('title')}")
            raise JavaScriptError(f"get_element_by_text: After all {self.poll_max_tries} attempts we only had a debug response.")
        elif data.get('matchType') == 'error':
            # This is the case where we received an error from the JavaScript
            self.print_func(f"JavaScript error in get_element_by_text: {data.get('error')}")
            self.print_func(f"Stack trace: {data.get('stack')}")
            raise JavaScriptError(f"get_element_by_text: After all {self.poll_max_tries} attempts we only had an error response.")
        else:
            # We don't know what happened but it was bad
            raise JavaScriptError(f"Unknown error in get_element_by_text")


    def poll_for_text(self, search_texts: Union[str, List[str]], query_selectors: Optional[Union[str, List[str]]] = None, click: bool = False) -> List[Dict[str, str]]:
        """
        Poll for text in the current Safari tab, trying multiple times if needed.
        Can search for multiple texts, trying each one for max_tries attempts.
        Uses instance variables for max_tries, wait_time, and print_func.
        
        Args:
            search_texts (Union[str, List[str]]): Text or list of texts to search for
            query_selectors (Optional[Union[str, List[str]]]): CSS query selector(s) to narrow down the search. If a list, must match length of search_texts.
            click (bool): If True, click the first matching element
            
        Returns:
            List[Dict[str, str]]: List of dictionaries containing tag and text for each matching element.
            Returns empty list if no matches found after all attempts.
        """
        # Convert single string to list for consistent handling
        if isinstance(search_texts, str):
            search_texts = [search_texts]
        if isinstance(query_selectors, str):
            query_selectors = [query_selectors]
        
        # Ensure query_selectors matches length of search_texts
        if query_selectors and len(query_selectors) != len(search_texts):
            raise ValueError("Number of query selectors must match number of search texts")
        
        # Use None for any missing query selectors
        query_selectors = query_selectors or [None] * len(search_texts)
        
        for search_text, query_selector in zip(search_texts, query_selectors):
            self.print_func(f"Searching for text: {search_text}")
            for attempt in range(1, self.poll_max_tries + 1):
                self.print_func(f"--Polling attempt {attempt}/{self.poll_max_tries} for '{search_text}'")
                
                # Try to find the text
                elements = self.get_element_by_text(search_text, query_selector, click=click)
                
                if elements and not isinstance(elements, dict):  # Only return if we have actual matches
                    self.print_func(f"Found text '{search_text}' in {len(elements)} elements on attempt {attempt}")
                    return elements
                
                if attempt < self.poll_max_tries:
                    self.print_func(f"Text '{search_text}' not found, waiting {self.poll_wait_time} seconds before next attempt...")
                    time.sleep(self.poll_wait_time)
        
        self.print_func("No matches found after all attempts")
        
        # Print which terms were found and which weren't
        found_terms = [term for term in search_texts if any(e['text'] == term for e in elements)]
        missing_terms = [term for term in search_texts if term not in found_terms]
        
        if found_terms:
            self.print_func("\nFound terms:")
            for term in found_terms:
                self.print_func(f"  - {term}")
                
        if missing_terms:
            self.print_func("\nMissing terms:")
            for term in missing_terms:
                self.print_func(f"  - {term}")
        
        return []

    def _close_front_safari_tab(self) -> None:
        """
        Close the first tab of the first Safari window using AppleScript.
        """
        script = '''
        tell application "System Events"
            repeat 20 times
                if exists (window 1 of process "Safari") then exit repeat
                delay 1
            end repeat
        end tell
        tell application "Safari"
            activate
            if (count of every tab of window 1) > 1 then
                set current_tab_index to index of current tab of window 1
                --display dialog "current_tab_index: " & current_tab_index
                close tab current_tab_index of window 1
            end if
        end tell
        '''
        try:
            result = applescript.run(script)
            # print(f"Result.err: {result.err}")
            # print(f"Result.code: {result.code}")
            # print(f"Result.out: {result.out}")
            if result.code != 0:
                self.print_func(f"Error closing Safari tab: {result.err}")
        except Exception as e:
            self.print_func(f"Error executing AppleScript to close tab: {str(e)}")

    def _close_all_safari_tabs(self) -> None:
        """
        Close all tabs of the first Safari window using AppleScript.
        """
        script = '''
        tell application "System Events"
            repeat 20 times
                if exists (window 1 of process "Safari") then exit repeat
                delay 1
            end repeat
        end tell
        set AppleScript's text item delimiters to ", "
        tell application "Safari"
            activate
            --display dialog "applescript_safari: _close_all_safari_tabs"
            --display dialog "Tabs of window 1: " & (get index of every tab of window 1 as string)
            --log "applescript_safari: _close_all_safari_tabs"
            --log "count of every tab of window 1: " & (count of every tab of window 1)
            --if (count of every tab of window 1) > 0 then
                close every tab of window 1
                --close every tab of every window
            --end if
            --display dialog "Tabs of window 1: " & (get index of every tab of window 1 as string)
        end tell
        '''
        try:
            result = applescript.run(script)
            # print(f"Result.err: {result.err}")
            # print(f"Result.code: {result.code}")
            # print(f"Result.out: {result.out}")
            if result.code != 0:
                self.print_func(f"Error closing Safari tab: {result.err}")
        except Exception as e:
            self.print_func(f"Error executing AppleScript to close tab: {str(e)}")

def get_escaped_js_for_text_search_v3(
    search_text: str,
    query_selector: str = "*",
    print_func: Optional[Callable] = None,
    click: bool = False,
    get_container_table: bool = False
) -> str:
    """
    Generate escaped JavaScript code to find elements containing the given text.
    
    This function creates JavaScript code that searches for elements containing the specified text,
    optionally within elements matching the provided query selector. The generated code can also
    click the first matching element if requested.
    
    Note: All curly braces in the generated JavaScript are doubled to escape them for both
    Python and AppleScript string interpolation.
    
    Args:
        search_text (str): The text to search for within elements
        query_selector (str, optional): CSS query selector to narrow down the search scope.
            Defaults to "*" to search all elements.
        print_func (Optional[Callable], optional): Function to use for printing debug information.
            Defaults to None.
        click (bool, optional): If True, clicks the first matching element. Defaults to False.
        get_container_table (bool, optional): If True, includes container table information in results.
            Defaults to False.
        
    Returns:
        str: Escaped JavaScript code ready to be used in AppleScript
    """
    search_text = unicodedata.normalize("NFKC", search_text).strip()
    print_func = print_func or _print_if_verbose
    print_func(f"get_escaped_js_for_text_search_v3 Searching for text: {search_text}")
    print_func(f"Using query selector: {query_selector}")
    if click:
        print_func("Click functionality enabled")
    if get_container_table:
        print_func("get_container_table functionality enabled")
    
    js_code = f'''
    (function() {{
        console.debug("Applescript Safari beginning injected javascript code");
        
        try {{
            const searchText = "{search_text}".normalize("NFKC").trim();
            const querySelector = "{query_selector}";
            const shouldClick = {str(click).lower()};
            const getContainerTable = {str(get_container_table).lower()};
            const elements = document.querySelectorAll(querySelector);
            var containerTable = 'shmoo';
            console.debug("getContainerTable:", getContainerTable);
            
            // Helper to get CSS selector string for an element
            function getCssSelector(el) {{
                let selector = el.tagName.toLowerCase();
                if (el.id) selector += '#' + el.id;
                if (el.className && el.className.trim()) {{
                    // Split class names and remove empty strings
                    const classes = el.className.trim().split(' ').filter(className => className !== '');
                    if (classes.length > 0) {{
                        selector += '.' + classes.join('.');
                    }}
                }}
                return selector;
            }}

            // Helper to get DOM path for an element
            function getDomPath(el) {{
                var stack = [];
                while (el.parentNode != null) {{
                    var sibCount = 0;
                    var sibIndex = 0;
                    for (var i = 0; i < el.parentNode.childNodes.length; i++) {{
                        var sib = el.parentNode.childNodes[i];
                        if (sib.nodeName == el.nodeName) {{
                            if (sib === el) {{
                                sibIndex = sibCount;
                            }}
                            sibCount++;
                        }}
                    }}
                    if (el.hasAttribute('id') && el.id != '') {{
                        stack.unshift(el.nodeName.toLowerCase() + '#' + el.id);
                    }} else if (sibCount > 1) {{
                        stack.unshift(el.nodeName.toLowerCase() + ':eq(' + sibIndex + ')');
                    }} else {{
                        stack.unshift(el.nodeName.toLowerCase());
                    }}
                    el = el.parentNode;
                }}
                return stack.slice(1); // removes the html element
            }}

            function getText(element) {{
                const directTextContent = Array.prototype.filter.call( // filter to text nodes
                    element.childNodes,
                    child => child.nodeType === Node.TEXT_NODE
                ).reduce((acc, node) => acc + node.textContent, ""); // accumulate the text content
                return directTextContent.normalize("NFKC").trim();
            }}

            // Find all elements containing the text recursively
            function findElementsWithText(element, searchText) {{
                if (!element) {{
                    console.debug("findElementsWithText: !element");
                    return [];
                }}
                const elementText = getText(element);
                //console.debug("findElementsWithText: element self-text:", elementText);
                //console.debug("findElementsWithText: searchText:", searchText);

                // Check if this element contains the text
                const containsText = elementText.includes(searchText);
                
                // If element contains the text, add it to results
                const results = [];
                if (containsText) {{
                    results.push(element);
                }}
                
                // Check children
                for (const child of element.children) {{
                    results.push(...findElementsWithText(child, searchText));
                }}
                return results;
            }}

            const matchingElements = [];
            for (const element of elements) {{
                matchingElements.push(...findElementsWithText(element, searchText));
            }}

            if (getContainerTable) {{
                console.debug("ApplescriptSafari getting container table:");
                containerTable = matchingElements[0].closest('table');
                containerTable = containerTable.outerHTML;
            }} else {{
                containerTable = '';
            }}
            
            // If we found matches, return them and optionally click the first one
            if (matchingElements.length > 0) {{
                console.debug("ApplescriptSafari found matching elements:");
                console.debug(matchingElements);
                if (shouldClick) {{
                    matchingElements[0].click();
                }}
                const matchingElements_json = matchingElements.map(el => ({{
                    text: el.textContent.trim(),
                    tag: el.tagName,
                    matchType: 'text',
                    selector: querySelector,
                    domPath: getDomPath(el),
                    containerTable: containerTable
                }}));
                console.debug(matchingElements_json);
                return JSON.stringify(matchingElements_json);
            }}
            
            // If no matches, return debug info
            return JSON.stringify({{
                matchType: 'debug',
                fullSource: document.documentElement.outerHTML,
                querySelector: querySelector,
                elementCount: elements.length,
                searchText: searchText,
                documentReady: document.readyState,
                url: window.location.href,
                title: document.title
            }});
        }} catch (error) {{
            console.debug('JavaScript Error in test_applescript_safari.py:');
            console.debug('Error message:', error.toString());
            console.debug('Stack trace:', error.stack);
            // Always return valid JSON, even in error cases
            return JSON.stringify({{
                matchType: 'error',
                error: error.toString(),
                stack: error.stack,
                documentReady: document.readyState,
                url: window.location.href,
                title: document.title
            }});
        }}
    }})();
    '''
    # First minimize the JavaScript
    minified_js = rjsmin.jsmin(js_code)
    # Then escape quotes and newlines for AppleScript
    minified_js = minified_js.replace('"', '\\"').replace('\n', ' ')
    return minified_js
    

if __name__ == "__main__":
    # Define test configurations
    test_configs = [
        {
            "name": "Google Trends Test",
            "search_terms": ["coffee", "tea"],
            "start_date": "2024-04-30",
            "end_date": "2024-05-30"
        },
        {
            "name": "Google Trends Test",
            "search_terms": ["car", "truck"],
            "start_date": "2024-04-30",
            "end_date": "2024-05-30"
        }
    ]
    
    # Run each test configuration
    # uncomment this to run all tests in the same instance of the API class
    # safari = ApplescriptSafari(print_func=print, close_tabs=True)
    safari = ApplescriptSafari(close_tabs=True)

    for config in test_configs:
        print(f"\n{'='*50}")
        print(f"Running {config['name']}")
        print(f"{'='*50}")
        
        # uncomment this to run each test in a new instance of the API class
        # safari = ApplescriptSafari(print_func=print)

        result = safari.search(
            search_term=config["search_terms"],
            start_date=config["start_date"],
            end_date=config["end_date"]
        ).standardize_data().data
        
        print(f"Results: {len(result)} records.")
        #print(result)

