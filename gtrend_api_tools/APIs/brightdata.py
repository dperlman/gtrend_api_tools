import time
import requests
from datetime import datetime
from typing import Union, List, Optional, Dict, Any
import pandas as pd
import unicodedata
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchContainer
from gtrend_api_tools.search_specs import SearchSpec, DateRange
from gtrend_api_tools.date_strings import parse_date_str, cleanup_date_str, standardize_date_range_start

class Brightdata(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://api.brightdata.com/request",
        method: str = "POST",
        **kwargs
    ):
        """
        Initialize the Brightdata class.
        
        Args:
            api_key (str): Your Brightdata API key
            api_endpoint (str): The Brightdata endpoint URL
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, method=method, **kwargs)

    def _request_headers(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        """
        Set up the request headers
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def _request_params(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        # Set up the request parameters
        params = None
        return params

    def _request_data(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        """
        Set up the request data
        """
        # We have to add the parameters brd_trends and brd_json the parameters for the base_trends_request_url
        # which is kind of weird, but that's how Brightdata wants it.
        brd_base_trends_request = internal_state.base_trends_request
        brd_base_trends_request.params['brd_trends'] = 'timeseries'
        brd_base_trends_request.params['brd_json'] = '1'
        brd_base_trends_request_prepared = brd_base_trends_request.prepare()
        data = {
            "zone": "trends",
            "url": brd_base_trends_request_prepared.url,
            "format": "raw"
        }
        return data


    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert Brightdata raw data to standardized format.
        Transforms the interest_over_time data into a list of dictionaries with date and values.
        
        Args:
            raw_data (Any): Raw data from Brightdata response
            
        Returns:
            Any: Standardized data in the common format
            
        Raises:
            ValueError: If raw data doesn't contain expected structure
        """
        if not raw_data:
            raise ValueError("No raw data provided")
            
        def check_for_interest_over_time(widget):
            if 'data' in widget and 'default' in widget['data'] and 'timelineData' in widget['data']['default']:
                return True
            return False

        raw_keywords = raw_data.get('keywords', [])
        keywords = [keyword['keyword'] for keyword in raw_keywords]

        widgets = raw_data.get('widgets', [])
        timeline = []
        for widget in widgets:
            if check_for_interest_over_time(widget):
                timeline = widget['data']['default']['timelineData']
                break

        # Transform the data into the standardized format
        data = []
        raw_date_list = []
        for entry in timeline:
            raw_date_list.append(cleanup_date_str(entry['formattedTime']))
            standardized_entry = {
                'date': standardize_date_range_start(entry['formattedTime']),
                'values': [
                    {
                        'value': entry['formattedValue'][i],
                        'query': keywords[i]
                    }
                    for i, _ in enumerate(entry['formattedValue'])
                ]
            }
            data.append(standardized_entry)
        
        self.logger.debug(f"Standardized data length: {len(data)}")
        return data

"""

curl https://api.brightdata.com/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 62b71d03b41ada34ac05851309d12411e2ddbc1ff2af32ae9a81f186204f015c" \
  -d '{
        "zone": "trends",
        "url": "https://trends.google.com/trends/explore?q=coffee,tea&geo=US&brd_trends=timeseries&brd_json=1",
        "format": "raw"
      }'
"""
