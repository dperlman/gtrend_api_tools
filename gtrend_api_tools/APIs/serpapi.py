import time
import requests
from datetime import datetime
from typing import Union, List, Optional, Dict, Any
import pandas as pd
import unicodedata
from gtrend_api_tools.APIs.base_classes import API_Call
from gtrend_api_tools.search_specs import SearchSpec, DateRange
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start

class SerpApi(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://serpapi.com/search",
        **kwargs
    ):
        """
        Initialize the SerpApi class.
        
        Args:
            api_key (str): Your SerpAPI API key
            api_endpoint (str): The SerpAPI endpoint URL
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, **kwargs)


    def _request_params(self) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'q': self.search_spec.term_string,
            'date': self.search_spec.str.search_range_ymd,
            'api_key': self.api_key,
            'engine': 'google_trends'
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
        if self.gprop:
            params['gprop'] = self.gprop
        return params


    def standardize_data(self) -> 'SerpApi':
        """
        Standardize the raw data into a common format.
        Transforms the interest_over_time data into a list of dictionaries with date and values.
        
        Returns:
            SerpApi: Returns self for method chaining
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

# def search_serpapi(
#     **kwargs
# ) -> Union[pd.DataFrame, Dict[str, Any]]:
#     """
#     Search Google Trends using the SerpAPI library.
    
#     Args:
#         **kwargs: Arguments passed to the parent class search method
#         **kwargs: Additional keyword arguments passed to API_Call
        
#     Returns:
#         Union[pd.DataFrame, Dict[str, Any]]: Standardized search results
#     """
#     serp = SerpApi(**locals())
#     return serp.search(**kwargs).standardize_data().data 