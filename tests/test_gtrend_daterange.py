#!/usr/bin/env python3
"""
Test script for GtrendDateRange class.
"""

import pytest
from datetime import datetime
from gtrend_api_tools.search_specs import GtrendDateRange


def test_gtrend_daterange_basic():
    """Test basic GtrendDateRange functionality."""
    
    # Test 1: Short range (should use hourly)
    dr1 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-01-04",
        verbose=False
    )
    assert dr1.granularity == 'h'
    assert dr1.get_max_units() == 192
    assert str(dr1).startswith("GtrendDateRange 2023-01-01 2023-01-04")
    
    # Test 2: Medium range (should use daily)
    dr2 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-04-11",
        verbose=False
    )
    assert dr2.granularity == 'D'
    assert dr2.get_max_units() == 270
    
    # Test 3: Long range (should use weekly)
    dr3 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2024-05-15",
        verbose=False
    )
    assert dr3.granularity == 'W'
    assert dr3.get_max_units() == 1900
    
    # Test 4: Very long range (should use monthly)
    dr4 = GtrendDateRange(
        start_date="2018-01-01",
        end_date="2024-01-01",
        verbose=False
    )
    assert dr4.granularity == 'M'
    assert dr4.get_max_units() == float('inf')


def test_gtrend_daterange_no_granularity_parameter():
    """Test that GtrendDateRange does not accept granularity parameter."""
    
    # Test that granularity parameter is not accepted
    with pytest.raises(TypeError):
        GtrendDateRange(
            start_date="2023-01-01",
            end_date="2023-04-11",
            granularity="W",  # This should raise TypeError
            verbose=False
        )


def test_gtrend_daterange_range_str():
    """Test GtrendDateRange with range_str parameter."""
    
    dr = GtrendDateRange(
        range_str="2023-01-01 - 2023-01-04",
        verbose=False
    )
    assert dr.granularity == 'h'
    assert dr.get_max_units() == 192


def test_gtrend_daterange_datetime_objects():
    """Test GtrendDateRange with datetime objects."""
    
    start_dt = datetime(2023, 1, 1)
    end_dt = datetime(2023, 1, 4)
    
    dr = GtrendDateRange(
        start_date=start_dt,
        end_date=end_dt,
        verbose=False
    )
    assert dr.granularity == 'h'
    assert dr.get_max_units() == 192


def test_gtrend_daterange_granularity_info():
    """Test that granularity_info is properly set."""
    
    dr = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-01-04",
        verbose=False
    )
    
    granularity_info = dr.get_granularity_info()
    assert isinstance(granularity_info, dict)
    assert 'granularity' in granularity_info
    assert 'datetime_index' in granularity_info
    assert 'period_index' in granularity_info
    assert 'max_units' in granularity_info
    assert granularity_info['granularity'] == 'h'


def test_gtrend_daterange_error_handling():
    """Test error handling in GtrendDateRange."""
    
    # Test with missing dates
    with pytest.raises(ValueError, match="Cannot initialize GtrendDateRange"):
        GtrendDateRange(verbose=False)
    
    # Test with only start_date
    with pytest.raises(ValueError, match="Cannot initialize GtrendDateRange"):
        GtrendDateRange(start_date="2023-01-01", verbose=False)
    
    # Test with only end_date
    with pytest.raises(ValueError, match="Cannot initialize GtrendDateRange"):
        GtrendDateRange(end_date="2023-01-04", verbose=False)


if __name__ == "__main__":
    # Run tests if script is executed directly
    test_gtrend_daterange_basic()
    test_gtrend_daterange_no_granularity_parameter()
    test_gtrend_daterange_range_str()
    test_gtrend_daterange_datetime_objects()
    test_gtrend_daterange_granularity_info()
    test_gtrend_daterange_error_handling()
    print("All tests passed!") 