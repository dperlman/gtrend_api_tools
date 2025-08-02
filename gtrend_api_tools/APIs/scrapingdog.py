import time
import requests
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
import pandas as pd
import unicodedata
from gtrend_api_tools.search_specs import DateRange
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchContainer
from gtrend_api_tools.date_strings import cleanup_date_str, standardize_date_range_start

class Scrapingdog(API_Call):
    def __init__(
        self,
        api_key: str,
        api_endpoint: Optional[str] = "https://api.scrapingdog.com/google_trends",
        **kwargs
    ):
        """
        Initialize the Scrapingdog class.
        
        Args:
            api_key (str): Your Scrapingdog API key
            api_endpoint (Optional[str]): The API endpoint URL. Defaults to "https://api.scrapingdog.com/google_trends"
            **kwargs: Additional keyword arguments passed to API_Call
        """
        super().__init__(api_key=api_key, api_endpoint=api_endpoint, **kwargs)

                
    def _request_params(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'query': internal_state.search_spec.term_string,
            'date': internal_state.search_spec.str.search_range_ymd,
            'api_key': self.api_key,
            'data_type': 'TIMESERIES'
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
            params['language'] = self.language
        if self.gprop:
            params['gprop'] = self.gprop
        return params


    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert Scrapingdog raw data to standardized format.
        Transforms the interest_over_time data into a list of dictionaries with date and values.
        
        Args:
            raw_data (Any): Raw data from Scrapingdog response
            
        Returns:
            Any: Standardized data in the common format
            
        Raises:
            ValueError: If raw data doesn't contain expected structure
        """
        if not raw_data:
            raise ValueError("No raw data provided")
            
        if 'interest_over_time' not in raw_data:
            raise ValueError("Raw data does not contain interest_over_time data")
            
        # Extract the timeline data
        timeline = raw_data['interest_over_time']['timeline_data']
        
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
        return data
