import pytest
from datetime import datetime, timedelta, timezone
from gtrend_api_tools.search_specs import GtrendDateRange


# Test some invalid inputs
def test_gdr_no_dates():
    """Test creating GtrendDateRange from no inputs should raise ValueError"""
    with pytest.raises(ValueError):
        GtrendDateRange()

def test_gdr_no_dates():
    """Test GtrendDateRange with freq or resolution should raise ValueError"""
    rs = "2020-03-21 - 2024-03-21"
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs, freq='D')
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs, resolution='D')

def test_gdr_invalid_datetime():
    """Test creating GtrendDateRange from invalid datetime inputs"""
    dt1 = datetime(2024, 3, 21, 14, 30, 45)
    dt2 = datetime(2020, 3, 21, 14, 30, 45) # end date is before start date
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(end=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1, end="invalid")
    with pytest.raises(ValueError):
        GtrendDateRange(start="invalid", end=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1, end=dt2)

def test_gdr_invalid_date_str():
    """Test creating GtrendDateRange from invalid string inputs"""
    dt1 = "2024-03-21"
    dt2 = "2020-03-21" # end date is before start date
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(end=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1, end="invalid")
    with pytest.raises(ValueError):
        GtrendDateRange(start="invalid", end=dt1)
    with pytest.raises(ValueError):
        GtrendDateRange(start=dt1, end=dt2)

def test_gdr_invalid_range_str():
    """Test creating GtrendDateRange from invalid range string inputs"""
    rs = "2024-03-21" # only one date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)
    rs = "hamburger - 2025-03-21" # really invalid first date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)
    rs = "2024-03-21 - hotdog" # really invalid second date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)
    rs = "2020-03-61 - 2025-03-21" # invalid first date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)
    rs = "2024-03-21 - 2025-03-61" # invalid second date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)
    rs = "2024-03-21 - 2020-03-21" # first date is after second date
    with pytest.raises(ValueError):
        GtrendDateRange(range_str=rs)

# Test some inputs with range_str
def test_gdr_range_str_hourly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 15, 00, 00, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2024-03-21T14 2024-03-28T15"
    assert dr.formatted_range_mdy == "03/21/2024T14 03/28/2024T15"
    assert dr.granularity == 'h'
    assert dr.freq == 'h'
    assert dr.resolution == 'h'

def test_gdr_range_str_daily_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match daily granularity: 2024-03-01 2024-03-28
    dr = GtrendDateRange(range_str="2024-03-01 2024-09-28")
    assert dr.original_range_str == "2024-03-01 2024-09-28"
    assert dr.start_dt == datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 9, 29, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2024-03-01 2024-09-29"
    assert dr.formatted_range_mdy == "03/01/2024 09/29/2024"
    assert dr.granularity == 'D'
    assert dr.freq == 'D'
    assert dr.resolution == 'D'

def test_gdr_range_str_weekly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match weekly granularity: 2024-01-07 2024-03-31 (Sundays)
    dr = GtrendDateRange(range_str="2020-01-07 2024-03-31")
    assert dr.original_range_str == "2020-01-07 2024-03-31"
    assert dr.start_dt == datetime(2020, 1, 5, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 4, 7, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2020-01-05 2024-04-07"
    assert dr.formatted_range_mdy == "01/05/2020 04/07/2024"
    assert dr.granularity == 'W'
    assert dr.freq == 'W-SAT'
    assert dr.resolution == 'D'

def test_gdr_range_str_monthly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match monthly granularity: 2023-01 2024-03
    dr = GtrendDateRange(range_str="2017-01-07 2024-03-31")
    assert dr.original_range_str == "2017-01-07 2024-03-31"
    assert dr.start_dt == datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2017-01 2024-04"
    assert dr.formatted_range_mdy == "01/2017 04/2024"
    assert dr.granularity == 'M'
    assert dr.freq == 'M'
    assert dr.resolution == 'M'
