import time
import requests
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
from gtrend_api_tools.search_specs import DateRange, SearchSpec
from gtrend_api_tools.APIs.base_classes import API_Call, TrendSearchContainer
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
    
    def _request_params(self, internal_state: TrendSearchContainer) -> Dict[str, Any]:
        # Set up the request parameters
        params = {
            'q': internal_state.search_spec.term_string,
            'api_key': self.api_key,
            'data_type': 'INTEREST_OVER_TIME',
            'time_period': 'custom',
            'time_period_min': internal_state.search_spec.str.search_start_mdy,
            'time_period_max': internal_state.search_spec.str.search_end_mdy,
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


    def raw_data_converter(self, raw_data: Any) -> Any:
        """
        Convert Serpwow raw data to standardized format.
        Transforms the trends_interest_over_time data into a list of dictionaries with date and values.
        
        Args:
            raw_data (Any): Raw data from Serpwow response
            
        Returns:
            Any: Standardized data in the common format
            
        Raises:
            ValueError: If raw data doesn't contain expected structure
        """
        if not raw_data:
            raise ValueError("No raw data provided")
            
        if 'trends_interest_over_time' not in raw_data:
            raise ValueError("Raw data does not contain trends_interest_over_time data")
            
        # Extract the timeline data
        timeline = raw_data['trends_interest_over_time']['data']
        
        # Transform the data into the standardized format
        data = []
        raw_date_list = []
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
        
        self.logger.debug(f"Standardized data length: {len(data)}")
        return data

    # def standardize_data(self) -> 'Serpwow':
    #     """
    #     Standardize the raw data into a common format.
    #     This method is kept for backward compatibility but now uses the TrendSearchResult system.
        
    #     Returns:
    #         Serpwow: Returns self for method chaining
    #     """
    #     # The standardization now happens automatically through the TrendSearchResult system
    #     # This method is kept for backward compatibility but doesn't need to do anything
    #     return self
