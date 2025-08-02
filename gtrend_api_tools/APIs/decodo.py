import time
import requests
from datetime import datetime
from typing import Union, List, Optional, Dict, Any
import pandas as pd
import unicodedata
import json
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchContainer
from gtrend_api_tools.search_specs import SearchSpec, DateRange
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start

class Decodo(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://scraper-api.decodo.com/v2/scrape",
        method: str = "POST",
        **kwargs
    ):
        """
        Initialize the Decodo class.
        
        Args:
            api_key (str): Your Decodo API key
            api_endpoint (str): The Decodo endpoint URL
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, method=method, **kwargs)

    def _request_headers(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        """
        Set up the request headers
        """
        headers = {
            'Authorization': f'Basic {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        return headers

    def _request_params(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        # Set up the request parameters
        params = None
        return params

    def _request_data(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        """
        Set up the request data
        """
        data = {
            "target": "google_trends_explore",
            "query": internal_state.search_spec.term_string,
            "geo": self.geo,
            "date_start": internal_state.search_spec.str.search_start_ymd,
            "date_end": internal_state.search_spec.str.search_end_ymd
        }
        return data


    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert Decodo raw data to standardized format.
        Transforms the interest_over_time data into a list of dictionaries with date and values.
        
        Args:
            raw_data (Any): Raw data from Decodo response
            
        Returns:
            Any: Standardized data in the common format
            
        Raises:
            ValueError: If raw data doesn't contain expected structure
        """
        if not raw_data:
            raise ValueError("No raw data provided")
        
        print(len(raw_data['results']))
        if 'results' not in raw_data or not raw_data['results']:
            print(json.dumps(raw_data, indent=4)[:3000])
            raise ValueError("Raw data does not contain results key for data")  
                  
        if 'content' not in raw_data['results'][0] or not raw_data['results'][0]['content']:
            raise ValueError("Raw data does not contain results.content data")
                              
        if 'interest_over_time' not in raw_data['results'][0]['content']:
            raise ValueError("Raw data does not contain interest_over_time data")
        
        interest_over_time = raw_data['results'][0]['content']['interest_over_time']
        # Transform the data into the standardized format
        raw_date_list = []
        data = []
        for time_idx in range(len(interest_over_time[0]['items'])):
            for item_idx in range(len(interest_over_time)):
                value_queries = []
                item = interest_over_time[item_idx]['items'][time_idx]
                date = item['time'] # we do this twice which is unnecessary but harmless
                value = item['value']
                query = interest_over_time[item_idx]['keyword']
                value_query = (value, query)
                value_queries.append(value_query)
            # this is intentionally outside the item_idx loop because we want to add the date only oncefor each item
            standardized_entry = {
                'date': standardize_date_range_start(date),
                'values': [
                    {
                        'value': value,
                        'query': query
                    }
                    for (value, query) in value_queries
                ]
            }
            data.append(standardized_entry)
            raw_date_list.append(cleanup_date_str(date))


        self.print_func(f"Standardized data length: {len(data)}")
        return data

"""

curl --request 'POST' \
        --url 'https://scraper-api.decodo.com/v2/scrape' \
        --header 'Accept: application/json' \
        --header 'Authorization: Basic 9441cfab3b5866ca03619e75c0116a9f5fbd7287873cc94b4f1965018ddfb818f1a79c8271944298e36a1da7ba2e4ab4152eecfdd6b674cae44e324cf1318e9c808a9635e7992c65da785e4f' \
        --header 'Content-Type: application/json' \
        --data '
    {
      "target": "google_trends_explore",
      "query": "seo optimization",
      "geo": "US",
      "date_start": "2020-01-01",
      "date_end": "2020-03-01"
    }
'
"""
