from typing import Dict, Union, Optional, Any, Tuple, List
from datetime import datetime, timedelta
import pandas as pd
import math
from gtrend_api_tools.granularity import GranularityManager
from gtrend_api_tools.utils import period_index_range_info
from gtrend_api_tools.search_specs import DateRange
from gtrend_api_tools.date_strings import CURRENT_DEFAULT_DT

def calculate_stagger(
    start: datetime,
    end: datetime,
    granularity: str = "D",
    search_unit_length: Optional[int] = None,
    stagger: int = 0,
    granularity_manager: Optional[GranularityManager] = None,
    truncate_end: bool = False
) -> List[List[Dict[str, Any]]]:
    """
    Calculate the stagger intervals for a given date range.

    Args:
        start_dt (datetime): Start date for the search
        end_dt (datetime): End date for the search
        granularity (str): Time granularity for results. Valid values are determined by granularity_rules.yaml:
            m, e, n, h, D, W, M
        search_unit_length (int): Number of time units in each search.
            If None, the value in granularity_rules.yaml for the given granularity is used.
        stagger (int): Number of overlapping intervals. 0 means no overlap, 1 means 50% overlap,
                        2 means 67% overlap, etc.
        granularity_manager (Optional[GranularityManager]): GranularityManager instance to use.
            If None, a new one will be created.
        truncate_end (bool): If True, the 'end' of each range will be truncated to the original end_dt.
            If False (default), ranges may extend beyond the original end_dt, and in fact may extend beyond the present (now) time.
            This is because the range size is always determined by max_records, so the last range may overshoot the requested end date.
            Set to True if you want all returned ranges to be strictly within the requested date range.

    Returns:
        List[List[Dict[str, Any]]]: List of lists of dictionaries, where each inner list represents a stagger group.
            Each dictionary contains:
            - spec_args: dict with start, end, freq, and resolution
            - group_idx: int - Which stagger group this search belongs to (0 to stagger)
            - interval_idx: int - Which interval within the group this is
            
    Raises:
        ValueError: If granularity is not valid or if search_unit_length cannot be determined
    """
    # Initialize granularity manager if not provided
    if granularity_manager is None:
        granularity_manager = GranularityManager()
    
    # Validate granularity
    if granularity not in granularity_manager.rules:
        raise ValueError(f"Invalid granularity: {granularity}. Must be one of: {list(granularity_manager.rules.keys())}")
    
    # Get granularity rule
    rule = granularity_manager.rules[granularity]
    # Get freq code from the granularity rule
    freq = rule['freq']
    # Check if the granularity has an infinite limit
    max_records = rule['max_records']
    # Get the search resolution
    resolution = rule['search_resolution']

    # Make an overall DateRange object for reference
    overall_date_range = DateRange(start=start, end=end, freq=freq, resolution=resolution)
    start_dt = overall_date_range.start_dt
    last_index_dt = overall_date_range.last_index_dt
    end_dt = overall_date_range.end_dt
    
    # TO DO: do we want to stagger these just for fun?
    if max_records == float('inf') or max_records == 'inf' or max_records == '.inf':
        # For infinite granularities, return a list of lists of dicts
        # Each inner list contains one dict for the entire range
        result = []
        for group_idx in range(stagger + 1):
            result.append([{
                'spec_args': {
                    'start': start_dt,
                    'end': end_dt,
                    'freq': freq,
                    'resolution': resolution
                },
                'group_idx': group_idx,
                'interval_idx': 0
            }])
        return result
    
    # 1. Build the initial ranges by iteratively creating PeriodIndex ranges
    ranges = []
    current_start = start_dt
    
    while current_start < end_dt:
        # Create a DateRange starting at current_start with max_records periods
        date_range = DateRange(start=current_start, periods=max_records, freq=freq, resolution=resolution)
        
        # Get the final end time from the DateRange instance
        range_end_dt = date_range.end_dt
        
        # Optionally truncate the end of the range
        range_dict = {
            'spec_args': {
                'start': current_start,
                'end': min(range_end_dt, end_dt) if truncate_end else range_end_dt,
                'freq': freq,
                'resolution': resolution
            }
        }
        ranges.append(range_dict)
        
        # Set current_start for next iteration (or to terminate if we're done)
        current_start = range_end_dt
    
    # 2. If stagger > 0, create additional stagger groups
    if stagger > 0:
        # a. Get the number of hours or days between original range end and final range end
        original_range_info = period_index_range_info(pd.period_range(start=start_dt, end=end_dt, freq=freq))
        final_range_info = period_index_range_info(pd.period_range(start=ranges[-1]['spec_args']['start'], end=ranges[-1]['spec_args']['end'], freq=freq))
        
        # Calculate the difference based on search_resolution
        if resolution == 'h':
            time_diff = int((final_range_info['end_dt'] - original_range_info['end_dt']).total_seconds() / 3600)
        elif resolution == 'D':
            time_diff = int((final_range_info['end_dt'] - original_range_info['end_dt']).days)
        else:
            raise ValueError(f"Unsupported search_resolution: {resolution}")
        
        # b. Divide by the number of remaining stagger groups
        stagger_offset = time_diff // stagger
        
        # c. For each stagger group, move start time back and create ranges
        for group_idx in range(1, stagger + 1):
            # Move start time back by the calculated offset
            if resolution == 'h':
                adjusted_start = start_dt - timedelta(hours=stagger_offset * group_idx)
            elif resolution == 'D':
                adjusted_start = start_dt - timedelta(days=stagger_offset * group_idx)
            
            # Create ranges for this stagger group
            group_ranges = []
            current_start = adjusted_start
            
            for range_idx in range(len(ranges)):
                # Create a DateRange starting at current_start with max_records periods
                date_range = DateRange(start=current_start, periods=max_records, freq=freq, resolution=resolution)
                
                # Get the final end time from the DateRange instance
                range_end_dt = date_range.end_dt
                
                # Optionally truncate the end of the range
                group_ranges.append({
                    'spec_args': {
                        'start': current_start,
                        'end': min(range_end_dt, end_dt) if truncate_end else range_end_dt,
                        'freq': freq,
                        'resolution': resolution
                    },
                    'group_idx': group_idx,
                    'interval_idx': range_idx
                })
                
                # Start the next range at the end of this one
                current_start = range_end_dt
            
            # Add this group's ranges to the result
            ranges.extend(group_ranges)
    
    # Add group_idx and interval_idx to all ranges (including original ranges)
    for range_idx, range_dict in enumerate(ranges):
        if 'group_idx' not in range_dict:
            range_dict['group_idx'] = 0
        if 'interval_idx' not in range_dict:
            range_dict['interval_idx'] = range_idx
    
    # Convert to the expected format: list of lists of dicts
    result = [[] for _ in range(stagger + 1)]
    for range_dict in ranges:
        group_idx = range_dict.get('group_idx', 0)
        result[group_idx].append(range_dict)
    
    return result
