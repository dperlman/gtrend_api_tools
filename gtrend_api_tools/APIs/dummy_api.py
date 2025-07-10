from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict, Any
import pandas as pd
from gtrend_api_tools.granularity import GranularityManager
from gtrend_api_tools.APIs.base_classes import API_Call
from gtrend_api_tools.APIs.api_utils import sinc_data
from gtrend_api_tools.date_strings import cleanup_date_str
import numpy as np

class DummyApi(API_Call):
    """
    A dummy API class that returns fake data for testing purposes.
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
        print_func: Optional[callable] = None,
        tor_control_password: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        fill_value: Union[str, int, float] = "sinc",
        **kwargs
    ):
        super().__init__(
            api_key=api_key,
            proxy=proxy,
            change_identity=change_identity,
            request_delay=request_delay,
            geo=geo,
            cat=cat,
            gprop=gprop,
            language=language,
            tz=tz,
            no_cache=no_cache,
            region=region,
            verbose=verbose,
            print_func=print_func,
            tor_control_password=tor_control_password,
            api_endpoint=api_endpoint,
            **kwargs
        )
        self.fill_value = fill_value

    def search(self, **kwargs) -> 'DummyApi':
        """
        Generate dummy data for testing purposes.
        
        Args:
            **kwargs: Arguments passed to the parent class search method
        
        Returns:
            DummyApi: Returns self for method chaining
        """

        # Call base class search method first to handle terms and dates
        super().search(**kwargs)
        # Get the processed search spec for dates
        spec = self.search_spec
            
        # Calculate number of days
        days = (spec.end_date_dt - spec.start_date_dt).days + 1
        
        # Generate dates
        dates = [spec.start_date_dt + timedelta(days=i) for i in range(days)]
        
        # Generate data in the format expected by standard_dict_to_df
        data = []
        
        if self.fill_value == "sinc":
            # Generate N sinc waves (one for each term)
            term_values = []
            for i, term in enumerate(spec.terms):
                # Each term gets a different number of zero crossings
                num_zero_crossings = i + 2  # First term gets 2, second gets 3, etc.
                values = sinc_data(num_zero_crossings, 100, 0, days)
                # Round to 2 decimal places
                values = np.round(values, 2)
                term_values.append(values)
            
            # Transpose the values so we have D groups of N terms
            term_values = np.array(term_values).T
            
            # Create entries for each date
            for i, date in enumerate(dates):
                entry = {
                    'date': date.strftime('%Y-%m-%d'),
                    'values': [
                        {
                            'query': term,
                            'value': float(term_values[i][j])  # Convert numpy float to Python float
                        }
                        for j, term in enumerate(spec.terms)
                    ]
                }
                data.append(entry)
        else:
            # Fill with constant value
            for date in dates:
                entry = {
                    'date': date.strftime('%Y-%m-%d'),
                    'values': [
                        {
                            'query': term,
                            'value': self.fill_value
                        }
                        for term in spec.terms
                    ]
                }
                data.append(entry)
        
        # Store the same data as raw_data for consistency
        self.raw_data = data
        
        
        return self 