"""
Google Trends API implementations package.
Contains implementations for various Google Trends APIs:
- SerpAPI (paid)
- SerpWow (paid)
- SearchAPI (paid)
- TrendsPy (free)
- SerpApiPy (paid)
- ApplescriptSafari (free)
- DummyApi (free)
- WinUiautoEdge (free, not implemented)
"""

from .api_utils import (
    change_tor_identity, standard_dict_to_df, load_api_config, api_string,
    available_apis, get_free_apis, get_paid_apis, get_api_info
)
from .serpapi import SerpApi
from .serpwow import Serpwow
from .searchapi import SearchApi
from .trendspy import TrendsPy
from .applescript_safari import ApplescriptSafari
from .dummy_api import DummyApi
from .win_uiauto_edge import WinUiautoEdge
from .brightdata import Brightdata
from .scrapingdog import Scrapingdog

# Make all API classes and utility functions available
__all__ = ['SerpApi', 'Serpwow', 'SearchApi', 'TrendsPy', 'ApplescriptSafari', 'DummyApi', 'WinUiautoEdge', 'Brightdata', 'Scrapingdog',
           'available_apis', 'get_free_apis', 'get_paid_apis', 'get_api_info',
           'change_tor_identity', 'standard_dict_to_df', 'api_string']

# Note: As far as I can tell, SerpApi and SearchApi always return the same data.
# Note that trendspy is very easily rate-limited, enough so that it might not even be usable.