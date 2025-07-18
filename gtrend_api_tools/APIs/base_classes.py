from typing import Union, List, Optional, Dict, Any, Callable
from datetime import datetime
import pandas as pd
from gtrend_api_tools.utils import _print_if_verbose, load_config
from gtrend_api_tools.APIs.api_utils import standard_dict_to_df
from gtrend_api_tools.search_specs import DateRange, SearchSpec
from gtrend_api_tools.date_strings import cleanup_date_str
import requests

class API_Call:
    """
    Base class for API calls to various Google Trends APIs.
    This class defines the common interface and parameters used across different API implementations.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        proxy: Optional[str] = None,
        change_identity: bool = True,
        request_delay: int = 4,
        geo: str = "US",
        cat: Optional[int] = None,
        gprop: Optional[str] = None,
        language: str = "en",
        tz: int = 420,
        no_cache: bool = False,
        region: Optional[str] = None,
        verbose: bool = False,
        print_func: Optional[Callable] = None,
        tor_control_password: Optional[str] = None,
        api_endpoint: Optional[str] = "https://trends.google.com/trends/explore", # put the actual API endpoint for the specific API subclass here
        base_trends_endpoint: Optional[str] = "https://trends.google.com/trends/explore", # leave this the same for reference purposes
        method: str = 'GET',
        granularity: str = 'D',
        **kwargs
    ):
        """
        Initialize the API_Call class.
        
        Args:
            api_key (Optional[str]): API key for the service. Required for some APIs, optional for others
            proxy (Optional[str]): The proxy to use. If None, will use proxy from config.yaml if available
            change_identity (bool): Whether to change Tor identity between iterations. Only used if proxy is provided
            request_delay (int): Delay between requests in seconds
            geo (str): Geographic location for the search (e.g. "US"). Defaults to "US"
            cat (Optional[int]): Category for the search. Defaults to None
            gprop (Optional[str]): Google property to search. Defaults to None
            language (str): Language for the search. Defaults to "en-US"
            tz (int): Timezone offset in minutes. Defaults to 420
            no_cache (bool): Whether to disable caching. Defaults to False
            region (Optional[str]): Region for the search. Defaults to None
            verbose (bool): Whether to print debug information
            print_func (Optional[Callable]): Function to use for printing debug information. If None, uses _print_if_verbose
            tor_control_password (Optional[str]): Password for Tor control port. Required if change_identity is True
            api_endpoint (Optional[str]): The API endpoint URL. Defaults to None
            granularity (str): The granularity of the date range. One of: 's' (seconds), 'm' (minutes), 'h' (hourly), 
                             'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly), 'Y' (yearly), 'X' (decade).
                             Defaults to 'D'.
            **kwargs: Additional keyword arguments specific to each API implementation
        """
        # Load config
        self.config = load_config()
        
        self.api_key = api_key
        self.proxy = proxy
        self.change_identity = change_identity
        self.request_delay = request_delay
        self.geo = geo
        self.cat = cat
        self.gprop = gprop
        self.language = language
        self.tz = tz
        self.no_cache = no_cache
        self.region = region
        self.verbose = verbose
        self.tor_control_password = tor_control_password
        self.api_endpoint = api_endpoint
        self.base_trends_endpoint = base_trends_endpoint
        self.method = method
        self.granularity = granularity
        self.kwargs = kwargs
        self._search_history = []
        self._raw_data_history = []
        self._data_history = []
        self._dataframe_history = []
        self._date_range = None

        # Create a closure that captures self.verbose
        def make_print_func(verbose: bool) -> callable:
            def print_with_verbose(message: str) -> None:
                _print_if_verbose(message, verbose)
            return print_with_verbose

        self.print_func = print_func if print_func is not None else make_print_func(self.verbose)

    def search(
        self,
        search_spec: Optional[SearchSpec] = None,
        **kwargs
    ) -> 'API_Call':
        """
        Search Google Trends using the API.
        
        Args:
            search_spec (Optional[SearchSpec]): Pre-configured search specification
            **kwargs: Arguments passed to SearchSpec constructor (search_term, start_date, end_date, date_range, granularity, verbose)
            
        Returns:
            API_Call: Returns self for method chaining. The raw data is stored in self.raw_data
        """
        self.print_func(f"Preparing {self.__class__.__name__} search request:")
        if search_spec is not None and isinstance(search_spec, SearchSpec):
            # Use provided search_spec directly
            self.search_spec = search_spec
        else:
            # Pass all kwargs to SearchSpec constructor
            self.search_spec = SearchSpec(**kwargs)
        self.print_func(f"Search spec: {self.search_spec}")

        self.print_func(f"  Search term: {self.search_spec.term_string}")
        self.print_func(f"  Search date range: {self.search_spec.str.search_range_ymd}")
    
        self.base_trends_request_url = self._base_trends_request_url()
        self.print_func(f"Base trends request URL: {self.base_trends_request_url}")

        if self.api_endpoint is None:
            return self # that's it, we're not going to do the requests if we don't have an endpoint
        self.request_headers = self._request_headers()
        self.print_func(f"Request headers: {self.request_headers}")

        self.request_params = self._request_params()
        self.print_func(f"Search params: {self.request_params}")
        
        self.request_data = self._request_data()
        self.print_func(f"Request data: {self.request_data}")

        # Prepare the request
        self.prepare_request()

        if self.__class__.__name__ == "API_Call":
            print(f"Base class {self.__class__.__name__} prepares a request directly to Google Trends.")
            print("We are about to send the request, but it is unlikely this will be useful in any way.")
            print("Google Trends URL:")
            print(self.prepared_request.url)

        # Make the request
        self.make_request()

        # Check if there's an error in the results
        if isinstance(self.raw_data, dict) and "error" in self.raw_data:
            error_msg = self.raw_data["error"]
            self.print_func(f"{self.__class__.__name__} Search failed: {error_msg}")
            raise Exception(error_msg)
        
        # Print success message
        self.print_func(f"{self.__class__.__name__} request sent successfully!")
        return self

    def _base_trends_request_url(self) -> str:
        """
        Construct the base request URL for Google Trends
        """
        params = {
            'q': self.search_spec.term_string,
            'date': self.search_spec.str.search_range_ymd
        }
        if self.geo:
            params['geo'] = self.geo
        if self.tz:
            params['tz'] = self.tz
        if self.region:
            params['region'] = self.region
        if self.cat:
            params['cat'] = self.cat
        if self.language:
            params['hl'] = self.language
        req = requests.Request('GET', self.base_trends_endpoint, params=params)
        self.base_trends_request = req
        self.prepared_base_trends_request = req.prepare()
        return self.prepared_base_trends_request.url

    def _request_headers(self) -> Dict[str, Any]:
        """
        Set up the request headers
        """
        headers = {}
        return headers

    def _request_params(self) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'q': self.search_spec.term_string,
            'date': self.search_spec.str.search_range_ymd
        }
        if self.geo:
            params['geo'] = self.geo
        if self.tz:
            params['tz'] = self.tz
        if self.region:
            params['region'] = self.region
        if self.cat:
            params['cat'] = self.cat
        if self.language:
            params['hl'] = self.language
        return params

    def _request_data(self) -> Dict[str, Any]:
        """
        Set up the request data
        """
        data = {}
        return data

    def prepare_request(self) -> None:
        """
        Prepare the request to print the full URL
        """
        kwargs = {}
        if self.request_params:
            kwargs['params'] = self.request_params
        if self.request_headers:
            kwargs['headers'] = self.request_headers
        if self.request_data:
            kwargs['json'] = self.request_data
        req = requests.Request(
            self.method,
            self.api_endpoint,
            **kwargs
        )
        self.request = req
        self.prepared_request = req.prepare()
        self.print_func(f"  Full request URL: {self.prepared_request.url}")

    def make_request(self) -> None:
        """
        Make the request to the API
        """
        # print(self.prepared_request.url)
        # print(self.prepared_request.headers)
        # print(self.prepared_request.body)
        # print(self.prepared_request.method)

        self.response = requests.Session().send(self.prepared_request)
        self.response.raise_for_status()
        self.raw_data = self.response.json()
        self.print_func("  Search successful!")
        #self.print_func(f"  Raw data: {self.raw_data}")


    def standardize_data(self) -> 'API_Call':
        """
        Standardize the raw data into a common format.
        Copies raw_data to data and extracts raw_date_list from the standardized format.
        
        Returns:
            API_Call: Returns self for method chaining
        """
        self.data = self.raw_data
        
        # Extract raw_date_list from the standardized data format
        raw_date_list = []
        for entry in self.raw_data:
            raw_date_list.append(cleanup_date_str(entry['date']))
        self.raw_date_list = raw_date_list
        
        return self

    def make_dataframe(self) -> 'API_Call':
        """
        Convert the standardized data to a pandas DataFrame.
        Uses standard_dict_to_df to create a DataFrame with a PeriodIndex.
        
        Returns:
            API_Call: Returns self for method chaining
        """
        self.dataframe = standard_dict_to_df(self.data)
        return self

    @property
    def raw_data(self) -> Any:
        """
        Get the raw data from the API response.
        
        Returns:
            Any: The raw API response data
            
        Raises:
            ValueError: If no raw data is available
        """
        if not self._raw_data_history:
            raise ValueError("No raw data available. Call search() first.")
        return self._raw_data_history[-1]

    @raw_data.setter
    def raw_data(self, value: Any) -> None:
        """
        Set the raw data and append it to the history.
        
        Args:
            value (Any): The raw data to set
        """
        self._raw_data_history.append(value)

    @property
    def data(self) -> Any:
        """
        Get the standardized data.
        
        Returns:
            Any: The standardized data
            
        Raises:
            ValueError: If no standardized data is available
        """
        if not self._data_history:
            raise ValueError("No standardized data available. Call standardize_data() first.")
        return self._data_history[-1]

    @data.setter
    def data(self, value: Any) -> None:
        """
        Set the standardized data and append it to the history.
        
        Args:
            value (Any): The standardized data to set
        """
        self._data_history.append(value)

    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the pandas DataFrame.
        
        Returns:
            pd.DataFrame: The pandas DataFrame
            
        Raises:
            ValueError: If no DataFrame is available
        """
        if not self._dataframe_history:
            raise ValueError("No DataFrame available. Call make_dataframe() first.")
        return self._dataframe_history[-1]

    @dataframe.setter
    def dataframe(self, value: pd.DataFrame) -> None:
        """
        Set the DataFrame and append it to the history.
        
        Args:
            value (pd.DataFrame): The DataFrame to set
        """
        self._dataframe_history.append(value)

    @property
    def raw_data_history(self) -> List[Any]:
        """
        Get the history of raw data.
        
        Returns:
            List[Any]: List of all raw data entries
        """
        return self._raw_data_history

    @property
    def data_history(self) -> List[Any]:
        """
        Get the history of standardized data.
        
        Returns:
            List[Any]: List of all standardized data entries
        """
        return self._data_history

    @property
    def dataframe_history(self) -> List[pd.DataFrame]:
        """
        Get the history of dataframes.
        
        Returns:
            List[pd.DataFrame]: List of all dataframe entries
        """
        return self._dataframe_history

    @property
    def search_history(self) -> List[Any]:
        """
        Get the search history.
        
        Returns:
            List[Any]: List of search terms used in previous searches
        """
        return self._search_history

    # @search_history.setter
    # def search_history(self, value: Any) -> None:
    #     """
    #     Add a search term to the search history.
        
    #     Args:
    #         value (Any): Search term to add to history
    #     """
    #     self._search_history.append(value)

    @property
    def search_spec(self) -> SearchSpec:
        """
        Get the current search specification.
        
        Returns:
            SearchSpec: The current search specification including terms and dates
            
        Raises:
            ValueError: If no search specification is available
        """
        if not self._search_history:
            raise ValueError("No search specification available. Call search() first.")
        return self._search_history[-1]

    @search_spec.setter
    def search_spec(self, spec: SearchSpec) -> None:
        """
        Set the current search specification and append it to the history.
        
        Args:
            spec (SearchSpec): Search specification to set
        """
        self._search_history.append(spec) 