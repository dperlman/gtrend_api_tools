#!/usr/bin/env python3
"""
Test script for the calculate_stagger function in granularity.py
"""

from datetime import datetime, timedelta
from gtrend_api_tools.granularity import calculate_stagger, GranularityManager

def test_calculate_stagger():
    """Test the calculate_stagger function with different granularities"""
    
    # Test dates
    start_dt = datetime(2023, 1, 1)
    end_dt = datetime(2023, 12, 31)
    
    print("Testing calculate_stagger function...")
    print(f"Date range: {start_dt} to {end_dt}")
    print()
    
    # Test different granularities
    granularities = ['m', 'e', 'n', 'h', 'D', 'W', 'M']
    
    for granularity in granularities:
        print(f"Testing granularity: {granularity}")
        try:
            # Test with default search_unit_length
            searches = calculate_stagger(
                start_dt=start_dt,
                end_dt=end_dt,
                granularity=granularity,
                stagger=1
            )
            
            print(f"  - Found {len(searches)} searches")
            print(f"  - First search: {searches[0]['start_date']}")
            print(f"  - Last search: {searches[-1]['start_date']}")
            
            # Group by stagger group
            groups = {}
            for search in searches:
                group_idx = search['group_idx']
                if group_idx not in groups:
                    groups[group_idx] = []
                groups[group_idx].append(search)
            
            print(f"  - Stagger groups: {len(groups)}")
            for group_idx, group_searches in groups.items():
                print(f"    Group {group_idx}: {len(group_searches)} searches")
            
        except Exception as e:
            print(f"  - ERROR: {e}")
        
        print()

if __name__ == "__main__":
    test_calculate_stagger() 