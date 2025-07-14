"""
Google Trends API Tools
A collection of tools for accessing Google Trends data through various APIs.
"""

__version__ = "0.1.0_alpha"

from .gtrend import Trends
from .utils import (
    load_config,
    save_to_csv,
    period_index_range_info
)
from .date_strings import parse_date_str, split_date_range_str, cleanup_date_str
from .search_specs import DateRange, SearchSpec
from .APIs import (
    available_apis,
    get_free_apis,
    get_paid_apis,
    get_api_info
)

__all__ = [
    'Trends',
    'load_config',
    'save_to_csv',
    'parse_date_str',
    'period_index_range_info',
    'DateRange',
    'SearchSpec',
    'available_apis',
    'get_free_apis',
    'get_paid_apis',
    'get_api_info'
]
