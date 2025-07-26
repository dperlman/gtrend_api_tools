from typing import Union, List, Optional, Dict, Any, Callable
from datetime import datetime
import pandas as pd
import inspect
import threading
import concurrent.futures
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
        search_spec: Optional[SearchSpec] = None,
        response: Optional[Any] = None,
        raw_data: Optional[Any] = None,
        converter: Optional[Callable] = None,
        data: Optional[Any] = None,
        dataframe: Optional[pd.DataFrame] = None
    ):
        """
        Initialize a TrendSearchResult.
        
        Args:
            raw_data (Any): The raw data from the API response
            converter (Callable[[Any], Any]): Function to convert raw_data to data. Required.
            data (Optional[Any]): The standardized data. If None, will be converted from raw_data using converter
            dataframe (Optional[pd.DataFrame]): The pandas DataFrame. If None, will be created from data
            search_spec (Optional[SearchSpec]): The search specification that produced this result
            response (Optional[Any]): The HTTP response object from the API call
        """
        # Validate converter
        if converter is None:
            self.converter = lambda x: x # this is a no-op converter
        elif not callable(converter): # if the converter is not callable, we raise an error
            raise ValueError("converter must be callable")
        
        self.raw_data = raw_data
        self.converter = converter
        self.data = data
        self.dataframe = dataframe
        self.search_spec = search_spec
        self.response = response
    
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


class TrendSearchErrorStatus:
    """
    A class to hold the errors from a Google Trends search attempt.
    
    This class encapsulates the error information from a single search operation.
    """
    
    def __init__(
        self,
        search_spec: SearchSpec,
        error: str = "",
        error_type: str = "",
        error_data: Optional[Any] = None,
        http_status_code: Optional[int] = None,
        is_error: bool = False
    ):
        """
        Initialize a TrendSearchErrorStatus.
        
        Args:
            search_spec (SearchSpec): The search specification that failed
            error (str): The error message
            error_type (str): The type/class of the error
            error_data (Optional[Any]): Any data returned with the error
            http_status_code (Optional[int]): HTTP status code if applicable
            is_error (bool): Whether this represents an error state (default: False)
        """
        self.search_spec = search_spec
        self.error = error
        self.error_type = error_type
        self.error_data = error_data
        self.http_status_code = http_status_code
        self.is_error = is_error
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"TrendSearchError({self.error_type}: {self.error})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the error."""
        return f"TrendSearchError(search_spec={self.search_spec}, error='{self.error}', error_type='{self.error_type}', http_status_code={self.http_status_code})"
    
    def __bool__(self) -> bool:
        """
        Boolean conversion for TrendSearchErrorStatus.
        
        Returns:
            bool: The value of is_error.
        """
        return self.is_error
    

class TrendSearchInternalState:
    """
    A class to hold the internal state during a search operation.
    
    This class encapsulates the temporary state that gets created during
    a search operation, making it suitable for thread-local storage.
    """
    
    def __init__(self, search_spec: Optional[SearchSpec] = None, search_result: Optional[TrendSearchResult] = None, search_error: Optional[TrendSearchErrorStatus] = None):
        self.search_spec = search_spec
        self.search_result = search_result
        self.search_error = search_error

        self.base_trends_request = None
        self.prepared_base_trends_request = None
        self.base_trends_request_url = None

        self.request_headers = None
        self.request_params = None
        self.request_data = None
        self.request = None
        self.prepared_request = None
        self.request_url = None
        # Status
        self.completed = False

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
        self._search_spec_history = []
        self._internal_state_history = []
        self._search_result_history = []
        self._search_error_history = []
        self._date_range = None
        self._history_lock = threading.Lock()

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
        # Set up the search parameters in the internal state that we track for thread safety
        internal_state = self.setup_search(search_spec, **kwargs)

        if self.__class__.__name__ == "API_Call":
            print(f"Base class {self.__class__.__name__} prepares a request directly to Google Trends.")
            print("We are about to send the request, but it is unlikely this will be useful in any way.")
            print("Google Trends URL:")
            print(internal_state.base_trends_request_url)

        # Make the request
        response_raw_data = self.send_request(internal_state)
        response = response_raw_data['response']
        raw_data = response_raw_data['raw_data']
        # Update the search result with the raw data
        internal_state.search_result.raw_data = raw_data
        internal_state.search_result.response = response
        self.print_func("  Search successful!")

        # Check if there's an error in the results
        if isinstance(raw_data, dict) and "error" in raw_data:
            error_msg = raw_data["error"]
            self.print_func(f"{self.__class__.__name__} Search failed: {error_msg}")
            # Update the existing TrendSearchErrorStatus object using the property
            current_error_status = internal_state.search_error
            current_error_status.error = error_msg
            current_error_status.error_type = "APIError"
            current_error_status.is_error = True
            raise Exception(error_msg)
        
        # Update success status in the existing TrendSearchErrorStatus object using the property
        current_error_status = self.search_error
        current_error_status.is_error = False
        
        # Print success message
        self.print_func(f"{self.__class__.__name__} request sent successfully!")
        return self


    def setup_search(
        self,
        search_spec: Optional[SearchSpec] = None,
        **kwargs
    ) -> TrendSearchInternalState:
        """
        Set up the search parameters and configuration.
        This method handles the common setup logic that all APIs need.
        
        Args:
            search_spec (Optional[SearchSpec]): Pre-configured search specification
            **kwargs: Arguments passed to SearchSpec constructor (search_term, start_date, end_date, date_range, granularity, verbose)
            
        Returns:
            TrendSearchInternalState: The internal state for this search
        """
        
        self.print_func(f"Preparing {self.__class__.__name__} search request:")
        if search_spec is not None and isinstance(search_spec, SearchSpec):
            # We are going to use the provided search_spec but first we will check if it matches our API
            # Check if the provided search_spec's API matches our API
            if self.api_string is not None and hasattr(search_spec, 'api') and search_spec.api != self.api_string:
                self.print_func(f"Warning: SearchSpec API '{search_spec.api}' doesn't match this API class '{self.api_string}'")
            # Use provided search_spec directly
            # i.e. search_spec = search_spec
        else:
            # Pass all kwargs to SearchSpec constructor, including the api parameter
            search_kwargs = kwargs.copy()
            if self.api_string is not None:
                self.print_func(f"Setting search_spec api to {self.api_string}")
                search_kwargs['api'] = self.api_string
            # Create a new search_spec with the provided kwargs
            search_spec = SearchSpec(**search_kwargs)

        # Set up our internal storage object
        # search_spec = search_spec we already have this
        search_result = TrendSearchResult(search_spec=search_spec, converter=self.raw_data_converter)
        search_error = TrendSearchErrorStatus(search_spec=search_spec)
        internal_state = TrendSearchInternalState(search_spec=search_spec, search_result=search_result, search_error=search_error) 
        self.initialize_history(search_spec, search_result, search_error, internal_state)
        
        self.print_func(f"Search spec: {search_spec}")
        self.print_func(f"  Search term: {search_spec.term_string}")
        self.print_func(f"  Search date range: {search_spec.str.search_range_ymd}")
    
        # Make the base trends request
        internal_state.base_trends_request = self._base_trends_request(internal_state)
        internal_state.prepared_base_trends_request = internal_state.base_trends_request.prepare()
        internal_state.base_trends_request_url = internal_state.prepared_base_trends_request.url
        self.print_func(f"Base trends request URL: {internal_state.base_trends_request_url}")

        # We may not have an API endpoint, in which case we're not going to do the requests
        if self.api_endpoint is None:
            return internal_state # that's it, we're not going to do the requests if we don't have an endpoint

        # Set up the API request
        internal_state.request_headers = self._request_headers(internal_state)
        self.print_func(f"Request headers: {internal_state.request_headers}")

        internal_state.request_params = self._request_params(internal_state)
        self.print_func(f"Search params: {internal_state.request_params}")
        
        internal_state.request_data = self._request_data(internal_state)
        self.print_func(f"Request data: {internal_state.request_data}")

        # Prepare the request
        internal_state.request = self._request(internal_state)
        internal_state.prepared_request = internal_state.request.prepare()
        internal_state.request_url = internal_state.prepared_request.url
        self.print_func(f"API request URL: {internal_state.request_url}")

        return internal_state 

    def initialize_history(self, search_spec: SearchSpec, search_result: TrendSearchResult, search_error: TrendSearchErrorStatus, internal_state: TrendSearchInternalState) -> None:
        """
        Initialize the history objects
        """
        with self._history_lock:
            self._search_spec_history.append(search_spec)
            self._search_result_history.append(search_result)
            self._search_error_history.append(search_error)
            self._internal_state_history.append(internal_state)

    def _base_trends_request(self, internal_state: TrendSearchInternalState) -> requests.Request:
        """
        Construct the base request URL for Google Trends
        """
        params = {
            'q': internal_state.search_spec.term_string,
            'date': internal_state.search_spec.str.search_range_ymd
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
        return req

    def _request_headers(self, internal_state: TrendSearchInternalState) -> Dict[str, Any]:
        """
        Set up the request headers
        """
        headers = {}
        return headers

    def _request_params(self, internal_state: TrendSearchInternalState) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'q': internal_state.search_spec.term_string,
            'date': internal_state.search_spec.str.search_range_ymd
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

    def _request_data(self, internal_state: TrendSearchInternalState) -> Dict[str, Any]:
        """
        Set up the request data
        """
        data = {}
        return data

    def _request(self, internal_state: TrendSearchInternalState) -> requests.Request:
        """
        Prepare the request to print the full URL
        """
        kwargs = {}
        if internal_state.request_params:
            kwargs['params'] = internal_state.request_params
        if internal_state.request_headers:
            kwargs['headers'] = internal_state.request_headers
        if internal_state.request_data:
            kwargs['json'] = internal_state.request_data
        req = requests.Request(
            self.method,
            self.api_endpoint,
            **kwargs
        )
        return req

    def send_request(self, internal_state: TrendSearchInternalState) -> None:
        """
        Make the request to the API
        """
        response = requests.Session().send(internal_state.prepared_request)
        response.raise_for_status()
        
        # Get raw data
        raw_data = response.json()
        return {'response': response, 'raw_data': raw_data}
    

    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert the raw data to a standardized format.
        """
        return raw_data

    # def standardize_data(self) -> 'API_Call':
    #     """
    #     Standardize the raw data into a common format.
    #     This method is kept for backward compatibility but now uses the TrendSearchResult system.
        
    #     Returns:
    #         API_Call: Returns self for method chaining
    #     """
    #     # The standardization now happens automatically through the TrendSearchResult system
    #     # This method is kept for backward compatibility but doesn't need to do anything
    #     return self

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
    def search_spec(self) -> SearchSpec:
        """
        Get the current search specification.
        
        Returns:
            SearchSpec: The current search specification including terms and dates
            
        Raises:
            ValueError: If no search specification is available
        """
        with self._history_lock:
            if not self._search_spec_history:
                raise ValueError("No search specification available. Call search() first.")
            return self._search_spec_history[-1]

    @search_spec.setter
    def search_spec(self, spec: SearchSpec) -> None:
        """
        Set the current search specification and append it to the history.
        
        Args:
            spec (SearchSpec): Search specification to set
        """
        with self._history_lock:
            self._search_spec_history.append(spec)

    @property
    def internal_state(self) -> TrendSearchInternalState:
        """
        Get the current internal state.
        
        Returns:
            TrendSearchInternalState: The current internal state
            
        Raises:
            ValueError: If no internal state is available
        """
        with self._history_lock:
            if not self._internal_state_history:
                raise ValueError("No internal state available. Call search() first.")
            return self._internal_state_history[-1]

    @internal_state.setter
    def internal_state(self, state: TrendSearchInternalState) -> None:
        """
        Set the current internal state and append it to the history.
        
        Args:
            state (TrendSearchInternalState): Internal state to set
        """
        with self._history_lock:
            self._internal_state_history.append(state)

    @property
    def search_result(self) -> TrendSearchResult:
        """
        Get the current search result.
        
        Returns:
            TrendSearchResult: The current search result
            
        Raises:
            ValueError: If no search result is available
        """
        with self._history_lock:
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
        with self._history_lock:
            self._search_result_history.append(result)

    @property
    def search_error(self) -> Optional[Dict[str, Any]]:
        """
        Get the current search error status.
        
        Returns:
            Optional[Dict[str, Any]]: The current search error status
            
        Raises:
            ValueError: If no search error status is available
        """
        with self._history_lock:
            if not self._search_error_history:
                raise ValueError("No search error status available. Call search() first.")
            return self._search_error_history[-1]

    @search_error.setter
    def search_error(self, error_status: Optional[Dict[str, Any]]) -> None:
        """
        Set the current search error status and append it to the history.
        
        Args:
            error_status (Optional[Dict[str, Any]]): Search error status to set
        """
        with self._history_lock:
            self._search_error_history.append(error_status)

    @property
    def search_spec_history(self) -> List[SearchSpec]:
        """
        Get the search specification history.
        
        Returns:
            List[SearchSpec]: List of all search specification entries
        """
        with self._history_lock:
            return self._search_spec_history.copy()

    @property
    def internal_state_history(self) -> List[Optional[TrendSearchInternalState]]:
        """
        Get the internal state history.
        
        Returns:
            List[Optional[TrendSearchInternalState]]: List of internal state objects for previous searches
        """
        with self._history_lock:
            return self._internal_state_history.copy()

    @property
    def search_result_history(self) -> List[TrendSearchResult]:
        """
        Get the history of search results.
        
        Returns:
            List[TrendSearchResult]: List of all search result entries
        """
        with self._history_lock:
            return self._search_result_history.copy()

    @property
    def search_error_history(self) -> List[Optional[Dict[str, Any]]]:
        """
        Get the search error history.
        
        Returns:
            List[Optional[Dict[str, Any]]]: List of error information for previous searches
        """
        with self._history_lock:
            return self._search_error_history.copy()


    
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
    
    def search_threaded_batch(self, spec_list: List[SearchSpec], max_workers: int = 10) -> List[TrendSearchResult]:
        """
        Execute multiple searches asynchronously using threads.
        
        Args:
            spec_list (List[SearchSpec]): List of search specifications to execute
            max_workers (int): Maximum number of worker threads
            
        Returns:
            List[TrendSearchResult]: List of search results in the same order as spec_list
        """
        if not spec_list:
            return []
        
        # Pre-allocate history lists and get starting index
        with self._history_lock:
            # Add all specs to history
            self._search_spec_history.extend(spec_list)
            
            # Get the starting index for this batch
            start_idx = len(self._search_result_history)
            
            # Pre-allocate result, error, and internal state lists with None
            self._search_result_history.extend([None] * len(spec_list))
            self._search_error_history.extend([None] * len(spec_list))
            self._internal_state_history.extend([None] * len(spec_list))
        
        # Execute batch with index-aware updates
        self._execute_batch_internal(spec_list, max_workers, start_idx)
        
        # Return the results from this batch
        return self._search_result_history[start_idx:]
    
    def _execute_batch_internal(self, spec_list: List[SearchSpec], max_workers: int, start_idx: int) -> None:
        """
        Internal method that handles the actual threaded execution.
        
        Args:
            spec_list (List[SearchSpec]): List of search specifications
            max_workers (int): Maximum number of worker threads
            start_idx (int): Starting index in the history lists
        """
        # Thread-local storage for API state
        thread_local = threading.local()
        
        def get_thread_api_state():
            """Get or create thread-local API state."""
            if not hasattr(thread_local, 'api_state'):
                # Create a copy of this instance for thread-local use
                thread_local.api_state = self.copy()
            return thread_local.api_state
        
        def execute_single_search(args):
            """Execute a single search in a thread."""
            batch_index, search_spec = args
            thread_api = get_thread_api_state()
            
            try:
                # Execute the search using the thread-local API
                thread_api.search(search_spec=search_spec)
                result = thread_api.search_result
                
                # Update the result at the correct position
                self._update_search_result(start_idx, batch_index, result, error=None)
                
            except Exception as e:
                # Update with error information
                error_info = {
                    'search_spec': search_spec,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                self._update_search_result(start_idx, batch_index, result=None, error=error_info)
        
        # Create arguments with batch indices
        search_args = [(i, spec) for i, spec in enumerate(spec_list)]
        
        # Execute with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(execute_single_search, args) for args in search_args]
            concurrent.futures.wait(futures)
    
    def _update_search_result(self, start_idx: int, batch_index: int, result: Optional[TrendSearchResult], error: Optional[Dict[str, Any]] = None, internal_state: Optional[TrendSearchInternalState] = None) -> None:
        """
        Thread-safe update of a single search result.
        
        Args:
            start_idx (int): Starting index in the history lists
            batch_index (int): Index within the current batch
            result (Optional[TrendSearchResult]): Search result (None if error)
            error (Optional[Dict[str, Any]]): Error information (None if success)
            internal_state (Optional[TrendSearchInternalState]): Internal state (None if not provided)
        """
        with self._history_lock:
            actual_index = start_idx + batch_index
            self._search_result_history[actual_index] = result
            self._search_error_history[actual_index] = error
            self._internal_state_history[actual_index] = internal_state 