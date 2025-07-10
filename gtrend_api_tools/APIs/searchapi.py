import time
import requests
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
import pandas as pd
import unicodedata
from gtrend_api_tools.search_specs import DateRange
from gtrend_api_tools.APIs.base_classes import API_Call
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start

class SearchApi(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: Optional[str] = "https://www.searchapi.io/api/v1/search",
        **kwargs
    ):
        """
        Initialize the SearchApi class.
        
        Args:
            api_key (str): Your SearchApi API key
            api_endpoint (Optional[str]): The API endpoint URL. Defaults to "https://www.searchapi.io/api/v1/search"
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, **kwargs)

    def search(self, **kwargs) -> 'SearchApi':
        """
        Search Google Trends using the SearchApi.
        
        Args:
            **kwargs: Arguments passed to the parent class search method
            
        Returns:
            SearchApi: Returns self for method chaining
        """
        # Call base class search method first to handle terms and dates
        super().search(**kwargs)
        # Get the processed search spec for dates
        spec = self.search_spec
        
        self.print_func(f"Sending SearchApi search request:")
        self.print_func(f"  Search term: {spec.term_string}")
        self.print_func(f"  Start date: {spec.start_date}")
        self.print_func(f"  End date: {spec.end_date}")
        
        try:
            # Set up the request parameters with only the allowed parameters
            params = {
                'engine': 'google_trends',
                'api_key': self.api_key,
                'data_type': 'TIMESERIES',
                'q': spec.term_string,
                'geo': self.geo,
                'tz': str(self.tz),
                'language': self.language
            }
            
            # Add optional parameters if they exist and are not None
            if hasattr(self, 'cat') and self.cat is not None:
                params['cat'] = str(self.cat)
            if hasattr(self, 'region') and self.region is not None:
                params['region'] = self.region
            if hasattr(self, 'gprop') and self.gprop is not None:
                params['gprop'] = self.gprop
            
            # Parse time range if provided
            params['time'] = spec.formatted_range_ymd
            self.print_func(f"  Time range: {spec.formatted_range_ymd}")
            
            # Make the HTTP GET request
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Parse the JSON response
            self.raw_data = response.json()
            
            # Check if there's an error in the results
            if isinstance(self.raw_data, dict) and "error" in self.raw_data:
                error_msg = self.raw_data["error"]
                self.print_func(f"  Search failed: {error_msg}")
                raise Exception(error_msg)
            
            self.print_func("  Search successful!")
            #self.print_func(self.raw_data)
            
            return self
                    
        except Exception as e:
            self.print_func(f"  Search failed: {str(e)}")
            raise

    def standardize_data(self) -> 'SearchApi':
        """
        Standardize the raw data into a common format.
        Transforms the interest_over_time data into a list of dictionaries with date and values.
        
        Returns:
            SearchApi: Returns self for method chaining
        """
        if not hasattr(self, 'raw_data') or not self.raw_data:
            raise ValueError("No raw data available. Call search() first.")
            
        if 'interest_over_time' not in self.raw_data:
            raise ValueError("Raw data does not contain interest_over_time data")
            
        # Extract the timeline data
        timeline = self.raw_data['interest_over_time']['timeline_data']
        
        # Transform the data into the standardized format
        raw_date_list = []
        data = []
        for entry in timeline:
            raw_date_list.append(cleanup_date_str(entry['date']))
            standardized_entry = {
                'date': standardize_date_range_start(entry['date']),
                'values': [
                    {
                        'value': item['extracted_value'],
                        'query': item['query']
                    }
                    for item in entry['values']
                ]
            }
            data.append(standardized_entry)
        self.print_func(f"Standardized data length: {len(data)}")
        self.raw_date_list = raw_date_list
        self.data = data
        return self

# def search_searchapi(
#     **kwargs
# ) -> Union[pd.DataFrame, Dict[str, Any]]:
#     """
#     Search Google Trends using the SearchApi.
    
#     Args:
#         **kwargs: Arguments passed to the parent class search method
#         **kwargs: Additional keyword arguments passed to API_Call
        
#     Returns:
#         Union[pd.DataFrame, Dict[str, Any]]: Standardized search results
#     """
#     searchapi = SearchApi(**locals())
#     return searchapi.search(**kwargs).standardize_data().data
