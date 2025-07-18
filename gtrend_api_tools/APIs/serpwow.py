import time
import requests
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
from gtrend_api_tools.search_specs import DateRange
from gtrend_api_tools.APIs.base_classes import API_Call
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start
import pandas as pd

class Serpwow(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: Optional[str] = "https://api.serpwow.com/live/search",
        **kwargs
    ):
        """
        Initialize the Serpwow class.
        
        Args:
            api_key (str): Your Serpwow API key
            api_endpoint (Optional[str]): The API endpoint URL. Defaults to "https://api.serpwow.com/live/search"
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, **kwargs)
    
    def _request_params(self) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'q': self.search_spec.term_string,
            'api_key': self.api_key,
            'data_type': 'INTEREST_OVER_TIME',
            'time_period': 'custom',
            'time_period_min': self.search_spec.str.search_start_mdy,
            'time_period_max': self.search_spec.str.search_end_mdy,
            'engine': 'google',
            'search_type': 'trends'
        }
        if self.geo:
            params['trends_geo'] = self.geo
        if self.tz:
            params['trends_tz'] = self.tz
        if self.region:
            params['trends_region'] = self.region
        if self.cat:
            params['trends_category'] = self.cat
        if self.language:
            params['hl'] = self.language
        if self.gprop:
            params['gprop'] = self.gprop
        return params


    def standardize_data(self) -> 'Serpwow':
        """
        Standardize the raw data into a common format.
        Transforms the trends_interest_over_time data into a list of dictionaries with date and values.
        
        Returns:
            Serpwow: Returns self for method chaining
        """
        if not hasattr(self, 'raw_data') or not self.raw_data:
            raise ValueError("No raw data available. Call search() first.")
            
        if 'trends_interest_over_time' not in self.raw_data:
            raise ValueError("Raw data does not contain trends_interest_over_time data")
            
        # Extract the timeline data
        timeline = self.raw_data['trends_interest_over_time']['data']
        
        # Transform the data into the standardized format
        raw_date_list = []
        data = []
        for entry in timeline:
            raw_date_list.append(cleanup_date_str(entry['date_formatted']))
            standardized_entry = {
                'date': standardize_date_range_start(entry['date_formatted']),
                'values': [
                    {
                        'value': item['value'],
                        'query': item['keyword']
                    }
                    for item in entry['values']
                ]
            }
            data.append(standardized_entry)
        self.print_func(f"Standardized data length: {len(data)}")
        self.raw_date_list = raw_date_list
        self.data = data
        return self

# def search_serpwow(**kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
#     """
#     Search Google Trends using the Serpwow API.
    
#     Args:
#         search_term (Union[str, List[str]]): The search term(s) to look up in Google Trends
#         start_date (Optional[Union[str, datetime]]): Start date for the search
#         end_date (Optional[Union[str, datetime]]): End date for the search
#         api_key (Optional[str]): The Serpwow API key. If None, will try to get from environment variable SERPWOW_API_KEY
#         **kwargs: Additional keyword arguments passed to API_Call
        
#     Returns:
#         Union[pd.DataFrame, Dict[str, Any]]: Standardized search results
#     """
#     serp = Serpwow(**locals())
#     return serp.search(**kwargs).standardize_data().data 