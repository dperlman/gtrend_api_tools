"""
Batch processing for Google Trends searches.
Provides functionality to execute multiple searches with different methods.
"""

from typing import Union, List, Dict, Any, Optional
from types import SimpleNamespace
from gtrend_api_tools.search_specs import SearchSpec
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchResult
from gtrend_api_tools.utils import load_config


class CompoundBatch:
    """
    A class for executing batch Google Trends searches with different processing methods.
    
    This class allows you to execute multiple searches using a main specification
    and a list of additional specifications, with different execution strategies.
    """
    def __init__(
        self,
        compound_spec_list: List[List[SearchSpec]],
        method: str = "simple",
        max_workers: int = 10
    ):
        """
        Initialize the CompoundBatch.
        
        Args:
            compound_spec_list (List[List[SearchSpec]]): List of lists of SearchSpec objects
            method (str): The execution method to use
            max_workers (int): Maximum number of workers for concurrent execution
        """
        self.compound_spec_list = compound_spec_list
        self.method = method
        self.max_workers = max_workers
        self.config = load_config()
        self.batch_config_list = self.validate_spec_list()
        
        # Create compound_result_list with the same shape as compound_spec_list
        # Fill each element with an empty TrendSearchResult() instance
        self.compound_result_list = []
        for inner_spec_list in self.compound_spec_list:
            inner_result_list = []
            for _ in inner_spec_list:
                inner_result_list.append(TrendSearchResult())
            self.compound_result_list.append(inner_result_list)
    
    def validate_spec_list(self) -> List[Dict[str, Any]]:
        """
        Validate the spec_list.
        
        For each inner list, ensures that every SearchSpec has the same .api property.
        Different sub-lists can have different .api properties.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries with 'api' and 'max_workers' keys
        """
        batch_configs = []
        
        for i, inner_list in enumerate(self.compound_spec_list):
            if not inner_list:
                raise ValueError(f"Compound spec list[{i}] is empty")
            
            # Get the api from the first SearchSpec in this inner list
            first_api = inner_list[0].api
            
            # Check that all SearchSpecs in this inner list have the same api
            api_mismatch = False
            for j, spec in enumerate(inner_list):
                if not isinstance(spec, SearchSpec):
                    raise ValueError(f"Compound spec list[{i}][{j}] is not a SearchSpec: {type(spec)}")
                
                if spec.api != first_api:
                    api_mismatch = True
                    break
            
            # Use None if there's an API mismatch, otherwise use the first API
            api_value = None if api_mismatch else first_api
            
            # Determine max_workers for this API
            if self.max_workers is not None:
                max_workers = self.max_workers
            else:
                # Get from config if API is valid, otherwise use a default
                if api_value is not None:
                    try:
                        max_workers = self.config['available_apis'][api_value]['default_concurrency']
                    except KeyError:
                        raise ValueError(f"API '{api_value}' not found in config or missing 'default_concurrency' setting")
                else:
                    # Use a default value when API is None
                    max_workers = self.max_workers
            
            batch_configs.append({
                'api': api_value,
                'max_workers': max_workers
            })
        
        return batch_configs


class TrendSearchBatch:
    """
    A class for executing batch Google Trends searches with different processing methods.
    
    This class allows you to execute multiple searches using a main specification
    and a list of additional specifications, with different execution strategies.
    """
    
    def __init__(
        self,
        main_spec: SearchSpec,
        spec_list: Union[List[SearchSpec], List[Dict[str, Any]], List[SimpleNamespace]],
        method: str = "iterate",
        max_workers: int = 10
    ):
        """
        Initialize the TrendSearchBatch.
        
        Args:
            main_spec (SearchSpec): The main search specification to use as a template
            spec_list (Union[List[SearchSpec], List[Dict[str, Any]], List[SimpleNamespace]]): 
                List of search specifications to process. Can be:
                - List of SearchSpec objects
                - List of dictionaries with search parameters
                - List of SimpleNamespace objects with search parameters
            method (str): The execution method to use. Options:
                - "iterate": Execute searches sequentially (default)
                - "async_poll": Execute searches asynchronously with polling
                - "async_webhook": Execute searches asynchronously with webhooks
        """
        self.main_spec = main_spec
        self.spec_list = spec_list
        self.method = method
        self.max_workers = max_workers

        # # Validate method parameter No, this is handled by the execute method
        # valid_methods = ["iterate", "async_internal_thread", "async_poll", "async_webhook"]
        # if method not in valid_methods:
        #     raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")
        
        # Process and validate spec_list
        self._process_spec_list()
        
        # Initialize results storage - now stores TrendSearchResult objects
        self.results: List[TrendSearchResult] = []
        self.errors: List[Dict[str, Any]] = []
        self.completed_count = 0
        self.total_count = len(self.spec_list)
    
    def _process_spec_list(self) -> None:
        """
        Process the spec_list to ensure all items are SearchSpec objects.
        
        Processing rules:
        1. If main_spec.api is None, fill it in with the first api from spec_list
        2. Check for api conflicts between main_spec and individual specs
        3. If it's a SearchSpec, use as-is
        4. If it's a DateRange or GtrendDateRange, create SearchSpec using main_spec's search_term
        5. If it's dict-like or SimpleNamespace-like:
           a. Use 'api' property if found, otherwise use from main_spec
           b. Use 'search_term', 'terms', or 'term_string' in that order, otherwise use from main_spec
           c. Use 'range_str' or ('start' and 'end'), otherwise use from main_spec
        """
        from gtrend_api_tools.search_specs import DateRange, GtrendDateRange
        
        # 1. If main_spec.api is None, fill it in with the first api from spec_list
        if not hasattr(self.main_spec, 'api') or self.main_spec.api is None:
            # Find the first spec with an api
            apis = [spec.api for spec in self.spec_list if spec and hasattr(spec, 'api') and spec.api is not None]
            api = apis[0] if apis else None
            self.main_spec.api = api
            print(f"Warning: main_spec.api was None, automatically set to '{api}' from spec_list")

        
        processed_specs = []
        
        for i, spec in enumerate(self.spec_list):
            # Check for api conflicts with main_spec
            if self.main_spec.api and self.main_spec.api != spec.api:
                print(f"Warning: spec_list[{i}] api '{spec.api}' conflicts with main_spec api '{self.main_spec.api}'")
            
            if isinstance(spec, SearchSpec):
                # 1. SearchSpec - use as-is, but fill in api if necessary
                if not hasattr(spec, 'api') and hasattr(self.main_spec, 'api'):
                    spec.api = self.main_spec.api
                processed_specs.append(spec)
                
            elif isinstance(spec, (DateRange, GtrendDateRange)):
                # 2. DateRange or GtrendDateRange - create SearchSpec with main_spec's search_term and api
                search_spec_params = {
                    'search_term': self.main_spec.term_string,
                    'date_range': spec
                }
                if hasattr(self.main_spec, 'api'):
                    search_spec_params['api'] = self.main_spec.api
                processed_specs.append(SearchSpec(**search_spec_params))
                
            elif hasattr(spec, '__getitem__') or hasattr(spec, '__dict__'):
                # 3. Dict-like or SimpleNamespace-like objects
                spec_dict = {}
                
                # Convert to dict if needed
                if hasattr(spec, '__dict__'):
                    # SimpleNamespace or object with __dict__
                    spec_dict = vars(spec)
                elif hasattr(spec, '__getitem__'):
                    # Dict-like object
                    spec_dict = dict(spec)
                else:
                    raise ValueError(f"Invalid spec_list[{i}] type: {type(spec)}")
                
                # Build SearchSpec parameters
                search_spec_params = {}
                
                # a. Handle 'api' property
                if 'api' in spec_dict:
                    search_spec_params['api'] = spec_dict['api']
                elif hasattr(self.main_spec, 'api'):
                    search_spec_params['api'] = self.main_spec.api
                
                # b. Handle search terms (search_term, terms, term_string in order)
                search_term = None
                if 'search_term' in spec_dict:
                    search_term = spec_dict['search_term']
                elif 'terms' in spec_dict:
                    search_term = spec_dict['terms']
                elif 'term_string' in spec_dict:
                    search_term = spec_dict['term_string']
                else:
                    search_term = self.main_spec.term_string
                
                search_spec_params['search_term'] = search_term
                
                # c. Handle date range (range_str or start/end)
                if 'range_str' in spec_dict:
                    search_spec_params['range_str'] = spec_dict['range_str']
                elif 'start' in spec_dict and 'end' in spec_dict:
                    search_spec_params['start'] = spec_dict['start']
                    search_spec_params['end'] = spec_dict['end']
                else:
                    # Use date range from main_spec
                    search_spec_params['start'] = self.main_spec.start_dt
                    search_spec_params['end'] = self.main_spec.end_dt
                
                # Create SearchSpec
                processed_specs.append(SearchSpec(**search_spec_params))
                
            else:
                raise ValueError(f"Invalid spec_list[{i}] type: {type(spec)}. Must be SearchSpec, DateRange, GtrendDateRange, dict-like, or SimpleNamespace-like")
        
        self.spec_list = processed_specs
    
    def execute(self, api_instance: API_Call) -> 'TrendSearchBatch':
        """
        Execute the batch search using the specified method.
        
        Args:
            api_instance (API_Call): The API instance to use for searches
            
        Returns:
            TrendSearchBatch: Returns self for method chaining
        """
        if self.method == "iterate":
            return self._execute_iterate(api_instance)
        elif self.method == "async_internal_thread":
            return self._execute_async_internal_thread(api_instance)
        elif self.method == "async_poll":
            return self._execute_async_poll(api_instance)
        elif self.method == "async_webhook":
            return self._execute_async_webhook(api_instance)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _execute_iterate(self, api_instance: API_Call) -> 'TrendSearchBatch':
        """
        Execute searches sequentially using iteration.
        
        Args:
            api_instance (API_Call): The API instance to use for searches
            
        Returns:
            TrendSearchBatch: Returns self for method chaining
        """
        # Reset results and progress
        self.results = []
        self.errors = []
        self.completed_count = 0
        
        # Execute each search specification sequentially
        for i, search_spec in enumerate(self.spec_list):
            try:
                # Execute the search using the provided API instance
                api_instance.search(search_spec=search_spec)
                
                # Get the search result from the API instance
                search_result = api_instance.search_result
                
                # Store the result
                self.results.append(search_result)
                self.errors.append(None)
                
                # Update progress
                self.completed_count += 1
                
            except Exception as e:
                self.results.append(None)
                # Store error information
                error_info = {
                    'index': i,
                    'search_spec': search_spec,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                self.errors.append(error_info)
                
                # Still increment completed count since we attempted this search
                self.completed_count += 1
        
        return self
        
    def _execute_async_internal_thread(self, api_instance: API_Call) -> 'TrendSearchBatch':
        """
        Execute searches concurrently using ThreadPoolExecutor.
        
        Args:
            api_instance (API_Call): The API instance to use for searches
            
        Returns:
            TrendSearchBatch: Returns self for method chaining
        """
        import concurrent.futures
        import threading
        
        # Reset results and progress
        self.results = []
        self.errors = []
        self.completed_count = 0
        
        # Temporary storage for results and errors in order
        temp_results = [None] * len(self.spec_list)
        temp_errors = [None] * len(self.spec_list)
        
        # Thread-local storage for API instances
        thread_local = threading.local()
        
        def get_thread_api_instance():
            """Get or create a thread-local API instance."""
            if not hasattr(thread_local, 'api_instance'):
                # Create a new instance of the same API class with the same configuration
                thread_local.api_instance = api_instance.copy()
            return thread_local.api_instance
        
        def execute_single_search(args):
            """Execute a single search in a thread."""
            index, search_spec = args
            thread_api = get_thread_api_instance()
            
            try:
                # Execute the search using the thread-local API instance
                thread_api.search(search_spec=search_spec)
                
                # Get the search result from the API instance
                search_result = thread_api.search_result
                
                # Store the result at the correct index (thread-safe with locks)
                with threading.Lock():
                    temp_results[index] = search_result
                    temp_errors[index] = None
                    self.completed_count += 1
                
                return None  # Success
                
            except Exception as e:
                # Store error information directly (thread-safe with locks)
                error_info = {
                    'index': index,
                    'search_spec': search_spec,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                
                with threading.Lock():
                    temp_results[index] = None
                    temp_errors[index] = error_info
                    self.completed_count += 1
                
                return None  # Error handled
        
        # Create arguments list with indices for proper ordering
        search_args = [(i, spec) for i, spec in enumerate(self.spec_list)]
        
        # Execute searches concurrently using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks and wait for completion
            futures = [executor.submit(execute_single_search, args) for args in search_args]
            
            # Wait for all futures to complete
            concurrent.futures.wait(futures)
        
        # Reconstruct results and errors lists in original order
        self.results = temp_results
        self.errors = temp_errors
        
        return self
    
    def _execute_async_poll(self, api_instance: API_Call) -> 'TrendSearchBatch':
        """
        Execute searches asynchronously with polling for completion.
        
        Args:
            api_instance (API_Call): The API instance to use for searches
            
        Returns:
            TrendSearchBatch: Returns self for method chaining
        """
        # TODO: Implement async execution with polling
        raise NotImplementedError("Async poll method not yet implemented")
    
    def _execute_async_webhook(self, api_instance: API_Call) -> 'TrendSearchBatch':
        """
        Execute searches asynchronously with webhook callbacks.
        
        Args:
            api_instance (API_Call): The API instance to use for searches
            
        Returns:
            TrendSearchBatch: Returns self for method chaining
        """
        # TODO: Implement async execution with webhooks
        raise NotImplementedError("Async webhook method not yet implemented")
    
    def get_results(self) -> List[TrendSearchResult]:
        """
        Get the results from the batch execution.
        
        Returns:
            List[TrendSearchResult]: List of search results
        """
        return self.results
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """
        Get any errors that occurred during batch execution.
        
        Returns:
            List[Dict[str, Any]]: List of error information
        """
        return self.errors
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get the current progress of the batch execution.
        
        Returns:
            Dict[str, Any]: Progress information including completed and total counts
        """
        return {
            'completed': self.completed_count,
            'total': self.total_count,
            'percentage': (self.completed_count / self.total_count * 100) if self.total_count > 0 else 0
        }
