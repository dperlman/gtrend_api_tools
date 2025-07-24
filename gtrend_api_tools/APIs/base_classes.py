from typing import Union, List, Optional, Dict, Any, Callable
from datetime import datetime
import pandas as pd
import inspect
from gtrend_api_tools.utils import _print_if_verbose, load_config
from gtrend_api_tools.APIs.api_utils import standard_dict_to_df, api_string
from gtrend_api_tools.search_specs import DateRange, SearchSpec
import requests
from gtrend_api_tools.granularity import GranularityManager

class TrendSearchResult:
    """
    A class to hold the results of a Google Trends search.
    
    This class encapsulates the raw data, standardized data, and DataFrame
    from a single search operation.
    """
    
    def __init__(
        self,
        raw_data: Any,
        converter: Callable[[Any], Any],
        data: Optional[Any] = None,
        dataframe: Optional[pd.DataFrame] = None,
        search_spec: Optional[SearchSpec] = None
    ):
        """
        Initialize a TrendSearchResult.
        
        Args:
            raw_data (Any): The raw data from the API response
            converter (Callable[[Any], Any]): Function to convert raw_data to data. Required.
            data (Optional[Any]): The standardized data. If None, will be converted from raw_data using converter
            dataframe (Optional[pd.DataFrame]): The pandas DataFrame. If None, will be created from data
            search_spec (Optional[SearchSpec]): The search specification that produced this result
        """
        # Validate converter
        if not callable(converter):
            raise ValueError("converter must be callable")
        
        # Handle raw_data and data logic
        if raw_data is None:
            if data is None:
                raise ValueError("Either raw_data or data must be provided")
            self.raw_data = data
        else:
            self.raw_data = raw_data
            
        self.converter = converter
        self._data = data
        self._dataframe = dataframe
        self.search_spec = search_spec
    
    
    @property
    def data(self) -> Any:
        """
        Get the standardized data.
        If data hasn't been explicitly set, converts raw_data using the converter.
        
        Returns:
            Any: The standardized data
        """
        # If _data is None (no explicit data provided), convert using converter
        if self._data is None:
            self._data = self.converter(self.raw_data)
        return self._data
    
    @data.setter
    def data(self, value: Any) -> None:
        """
        Set the standardized data.
        
        Args:
            value (Any): The standardized data to set
        """
        self._data = value
        # Reset dataframe since data changed
        self._dataframe = None
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the pandas DataFrame. Creates it if it doesn't exist.
        
        Returns:
            pd.DataFrame: The pandas DataFrame
            
        Raises:
            ValueError: If no standardized data is available
        """
        if self._dataframe is None:
            self._dataframe = standard_dict_to_df(self.data)
        return self._dataframe
    
    @dataframe.setter
    def dataframe(self, value: pd.DataFrame) -> None:
        """
        Set the DataFrame.
        
        Args:
            value (pd.DataFrame): The DataFrame to set
        """
        self._dataframe = value
    
    def __str__(self) -> str:
        """String representation of the result."""
        data_type = type(self._data).__name__ if self._data is not None else "None"
        return f"TrendSearchResult(raw_data_type={type(self.raw_data).__name__}, data_type={data_type}, has_dataframe={self._dataframe is not None})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the result."""
        return f"TrendSearchResult(raw_data={self.raw_data}, data={self.data}, dataframe={self._dataframe})"

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
        emulate_api: bool = False,
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
        self.api_string = self._api_string()
        self.emulate_api = emulate_api or self.api_string # if we are not emulating an API, we use the actual API string
        self.kwargs = kwargs
        self._search_history = []
        self._search_result_history = []
        self._date_range = None

        # Create a closure that captures self.verbose
        def make_print_func(verbose: bool) -> callable:
            def print_with_verbose(message: str) -> None:
                _print_if_verbose(message, verbose)
            return print_with_verbose

        self.print_func = print_func if print_func is not None else make_print_func(self.verbose)

        # Store a granularity manager for this API
        # If we are emulating an API, we need to use the API string that is being emulated
        # Otherwise, we use the API string that is actually being used
        self.granularity_manager = GranularityManager(api=self.emulate_api)

    def setup_search(
        self,
        search_spec: Optional[SearchSpec] = None,
        **kwargs
    ) -> 'API_Call':
        """
        Set up the search parameters and configuration.
        This method handles the common setup logic that all APIs need.
        
        Args:
            search_spec (Optional[SearchSpec]): Pre-configured search specification
            **kwargs: Arguments passed to SearchSpec constructor (search_term, start_date, end_date, date_range, granularity, verbose)
            
        Returns:
            API_Call: Returns self for method chaining
        """
        
        self.print_func(f"Preparing {self.__class__.__name__} search request:")
        if search_spec is not None and isinstance(search_spec, SearchSpec):
            # Check if the provided search_spec's API matches our API
            if self.api_string is not None and hasattr(search_spec, 'api') and search_spec.api != self.api_string:
                self.print_func(f"Warning: SearchSpec API '{search_spec.api}' doesn't match this API class '{self.api_string}'")
            # Use provided search_spec directly
            self.search_spec = search_spec
        else:
            # Pass all kwargs to SearchSpec constructor, including the api parameter
            search_kwargs = kwargs.copy()
            if self.api_string is not None:
                self.print_func(f"Setting search_spec api to {self.api_string}")
                search_kwargs['api'] = self.api_string
            self.search_spec = SearchSpec(**search_kwargs)

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

        return self

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
        # Set up the search parameters
        self.setup_search(search_spec, **kwargs)

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
        
        # Get raw data
        raw_data = self.response.json()
        
        # Create TrendSearchResult with raw data and search_spec (standardization will be handled later)
        self.search_result = TrendSearchResult(
            raw_data=raw_data,
            search_spec=self.search_spec,
            converter=self.raw_data_converter
        )
        
        self.print_func("  Search successful!")
        #self.print_func(f"  Raw data: {raw_data}")

    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert the raw data to a standardized format.
        """
        return raw_data

    def standardize_data(self) -> 'API_Call':
        """
        Standardize the raw data into a common format.
        This method is kept for backward compatibility but now uses the TrendSearchResult system.
        
        Returns:
            API_Call: Returns self for method chaining
        """
        # The standardization now happens automatically through the TrendSearchResult system
        # This method is kept for backward compatibility but doesn't need to do anything
        return self

    def _api_string(self) -> Optional[str]:
        """
        Get the API string identifier for this class from available_apis configuration.
        
        Returns:
            Optional[str]: The API string (e.g., 'serpapi', 'trendspy') or None if not found
        """
        # Get the class name
        class_name = self.__class__.__name__
        return api_string(class_name)

    @property
    def raw_data(self) -> Any:
        """
        Get the raw data from the API response.
        
        Returns:
            Any: The raw API response data
            
        Raises:
            ValueError: If no search has been performed yet
        """
        try:
            return self.search_result.raw_data
        except ValueError as e:
            raise ValueError("No search has been performed yet. Call search() first.") from e

    @property
    def data(self) -> Any:
        """
        Get the standardized data.
        
        Returns:
            Any: The standardized data
            
        Raises:
            ValueError: If no search has been performed yet
        """
        try:
            return self.search_result.data
        except ValueError as e:
            raise ValueError("No search has been performed yet. Call search() first.") from e

    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the pandas DataFrame.
        
        Returns:
            pd.DataFrame: The pandas DataFrame
            
        Raises:
            ValueError: If no search has been performed yet
        """
        try:
            return self.search_result.dataframe
        except ValueError as e:
            raise ValueError("No search has been performed yet. Call search() first.") from e



    @property
    def search_result_history(self) -> List[TrendSearchResult]:
        """
        Get the history of search results.
        
        Returns:
            List[TrendSearchResult]: List of all search result entries
        """
        return self._search_result_history

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
    def search_result(self) -> TrendSearchResult:
        """
        Get the current search result.
        
        Returns:
            TrendSearchResult: The current search result
            
        Raises:
            ValueError: If no search result is available
        """
        if not self._search_result_history:
            raise ValueError("No search result available. Call search() first.")
        return self._search_result_history[-1]

    @search_result.setter
    def search_result(self, result: TrendSearchResult) -> None:
        """
        Set the current search result and append it to the history.
        
        Args:
            result (TrendSearchResult): Search result to set
        """
        self._search_result_history.append(result)

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
    
    def copy(self) -> 'API_Call':
        """
        Create a copy of this API instance with the same initialization parameters.
        
        Returns:
            API_Call: A new instance of the same class with identical configuration
        """
        # Get the constructor signature
        sig = inspect.signature(self.__class__.__init__)
        
        # Build kwargs dict with all parameters
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue  # Skip self parameter
            if hasattr(self, param_name):
                kwargs[param_name] = getattr(self, param_name)
        
        # Create new instance
        return type(self)(**kwargs) 