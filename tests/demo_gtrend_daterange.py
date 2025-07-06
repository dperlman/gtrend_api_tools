#!/usr/bin/env python3
"""
Demonstration script for GtrendDateRange class.
"""

from datetime import datetime
from gtrend_api_tools.search_specs import GtrendDateRange

def demo_gtrend_daterange():
    """Demonstrate the GtrendDateRange class functionality."""
    
    print("GtrendDateRange Class Demonstration")
    print("=" * 50)
    
    # Demo 1: Short range (should use hourly)
    print("\nDemo 1: Short range (3 days) - should use hourly")
    dr1 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-01-04",
        verbose=True
    )
    print(f"DateRange: {dr1}")
    print(f"Granularity: {dr1.granularity}")
    print(f"Max units: {dr1.get_max_units()}")
    
    # Demo 2: Medium range (should use daily)
    print("\nDemo 2: Medium range (100 days) - should use daily")
    dr2 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-04-11",
        verbose=True
    )
    print(f"DateRange: {dr2}")
    print(f"Granularity: {dr2.granularity}")
    print(f"Max units: {dr2.get_max_units()}")
    
    # Demo 3: Long range (should use weekly)
    print("\nDemo 3: Long range (500 days) - should use weekly")
    dr3 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2024-05-15",
        verbose=True
    )
    print(f"DateRange: {dr3}")
    print(f"Granularity: {dr3.granularity}")
    print(f"Max units: {dr3.get_max_units()}")
    
    # Demo 4: Very long range (should use monthly)
    print("\nDemo 4: Very long range (2000+ days) - should use monthly")
    dr4 = GtrendDateRange(
        start_date="2018-01-01",
        end_date="2024-01-01",
        verbose=True
    )
    print(f"DateRange: {dr4}")
    print(f"Granularity: {dr4.granularity}")
    print(f"Max units: {dr4.get_max_units()}")
    
    # Demo 5: Note about explicit granularity
    print("\nDemo 5: Note about explicit granularity")
    print("GtrendDateRange does not accept a granularity parameter.")
    print("It always automatically calculates the appropriate granularity.")
    print("If you need to specify granularity explicitly, use the DateRange base class:")
    print("  from gtrend_api_tools.search_specs import DateRange")
    print("  dr = DateRange(start_date='2023-01-01', end_date='2023-04-11', granularity='W')")
    
    # Demo 6: Using range_str
    print("\nDemo 6: Using range_str")
    dr6 = GtrendDateRange(
        range_str="2023-01-01 - 2023-01-04",
        verbose=True
    )
    print(f"DateRange: {dr6}")
    print(f"Granularity: {dr6.granularity}")
    
    # Demo 7: Using datetime objects
    print("\nDemo 7: Using datetime objects")
    start_dt = datetime(2023, 1, 1)
    end_dt = datetime(2023, 1, 4)
    dr7 = GtrendDateRange(
        start_date=start_dt,
        end_date=end_dt,
        verbose=True
    )
    print(f"DateRange: {dr7}")
    print(f"Granularity: {dr7.granularity}")
    
    # Demo 8: Show granularity info
    print("\nDemo 8: Granularity information")
    granularity_info = dr1.get_granularity_info()
    print("Granularity info keys:", list(granularity_info.keys()))
    print("Datetime index length:", len(granularity_info['datetime_index']))
    print("Period index length:", len(granularity_info['period_index']))
    
    print("\n" + "=" * 50)
    print("Demonstration completed!")

if __name__ == "__main__":
    demo_gtrend_daterange() 