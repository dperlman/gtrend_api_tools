import pytest
from datetime import datetime, timedelta, timezone
from gtrend_api_tools.search_specs import DateRange, GtrendDateRange, SearchSpec

# # useful test data
# dt1 = datetime(2024, 3, 21, 14, 30, 45, tzinfo=timezone.utc)
# dt2 = datetime(2024, 3, 28, 14, 30, 45, tzinfo=timezone.utc)
# dt3 = datetime(2020, 3, 21, 14, 30, 45, tzinfo=timezone.utc)
# ds1 = "2024-03-21T14:30:45"
# ds2 = "2024-03-28T14:30:45"
# ds3 = "2020-03-21T14:30:45"


########################################################
# Test DateRange class
########################################################

# Test some invalid inputs
def test_date_range_no_dates():
    """Test creating DateRange from no inputs should raise ValueError"""
    with pytest.raises(ValueError):
        DateRange()

def test_date_range_invalid_datetime():
    """Test creating DateRange from invalid datetime inputs"""
    dt1 = datetime(2024, 3, 21, 14, 30, 45)
    dt2 = datetime(2020, 3, 21, 14, 30, 45) # end date is before start date
    with pytest.raises(ValueError):
        DateRange(start=dt1)
    with pytest.raises(ValueError):
        DateRange(end=dt1)
    with pytest.raises(ValueError):
        DateRange(start=dt1, end="invalid")
    with pytest.raises(ValueError):
        DateRange(start="invalid", end=dt1)
    with pytest.raises(ValueError):
        DateRange(start=dt1, end=dt2)

def test_date_range_invalid_date_str():
    """Test creating DateRange from invalid string inputs"""
    dt1 = "2024-03-21"
    dt2 = "2020-03-21" # end date is before start date
    with pytest.raises(ValueError):
        DateRange(start=dt1)
    with pytest.raises(ValueError):
        DateRange(end=dt1)
    with pytest.raises(ValueError):
        DateRange(start=dt1, end="invalid")
    with pytest.raises(ValueError):
        DateRange(start="invalid", end=dt1)
    with pytest.raises(ValueError):
        DateRange(start=dt1, end=dt2)

def test_date_range_invalid_range_str():
    """Test creating DateRange from invalid range string inputs"""
    rs = "2024-03-21" # only one date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)
    rs = "hamburger - 2025-03-21" # really invalid first date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)
    rs = "2024-03-21 - hotdog" # really invalid second date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)
    rs = "2020-03-61 - 2025-03-21" # invalid first date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)
    rs = "2024-03-21 - 2025-03-61" # invalid second date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)
    rs = "2024-03-21 - 2020-03-21" # first date is after second date
    with pytest.raises(ValueError):
        DateRange(range_str=rs)

# Test some inputs with range_str
def test_date_range_range_str():
    """Test with range_str and default freq and resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 29, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T00 2024-03-29T00"
    assert dr.str.full_range_mdy == "03/21/2024T00 03/29/2024T00"
    assert dr.str.index_range_ymd == "2024-03-21T00 2024-03-28T00"
    assert dr.str.index_range_mdy == "03/21/2024T00 03/28/2024T00"
    assert dr.freq == 'D'
    assert dr.resolution == 'h'



# Now a whole series to try all the different freqs and resolutions

def test_date_range_range_str_minutes_freq():
    """Test with range_str, minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-21T18:30:45", freq='min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-21T18:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 21, 18, 31, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30:00 2024-03-21T18:31:00"
    assert dr.str.full_range_mdy == "03/21/2024T14:30:00 03/21/2024T18:31:00"
    assert dr.str.index_range_ymd == "2024-03-21T14:30:00 2024-03-21T18:30:00"
    assert dr.str.index_range_mdy == "03/21/2024T14:30:00 03/21/2024T18:30:00"
    assert dr.freq == 'min'
    assert dr.resolution == 's'

def test_date_range_range_str_8minutes_freq():
    """Test with range_str, 8 minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-23T01:30:45", freq='8min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-23T01:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 23, 1, 34, 00, tzinfo=timezone.utc) # The last 8min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T14:30:00 2024-03-23T01:34:00"
    assert dr.str.full_range_mdy == "03/21/2024T14:30:00 03/23/2024T01:34:00"
    assert dr.str.index_range_ymd == "2024-03-21T14:30:00 2024-03-23T01:26:00"
    assert dr.str.index_range_mdy == "03/21/2024T14:30:00 03/23/2024T01:26:00"
    assert dr.freq == '8min'
    assert dr.resolution == 's'

def test_date_range_range_str_16minutes_granularity():
    """Test with range_str, sixteen minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 13, 42, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T14:30:00 2024-03-24T13:42:00"
    assert dr.str.full_range_mdy == "03/21/2024T14:30:00 03/24/2024T13:42:00"
    assert dr.str.index_range_ymd == "2024-03-21T14:30:00 2024-03-24T13:26:00"
    assert dr.str.index_range_mdy == "03/21/2024T14:30:00 03/24/2024T13:26:00"
    assert dr.freq == '16min'
    assert dr.resolution == 's'

def test_date_range_range_str_hourly_granularity():
    """Test with range_str, hourly freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-29T13:30:45", freq='h', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-29T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 29, 14, 00, 00, tzinfo=timezone.utc) # The last hour period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T14:00:00 2024-03-29T14:00:00"
    assert dr.str.full_range_mdy == "03/21/2024T14:00:00 03/29/2024T14:00:00"
    assert dr.str.index_range_ymd == "2024-03-21T14:00:00 2024-03-29T13:00:00"
    assert dr.str.index_range_mdy == "03/21/2024T14:00:00 03/29/2024T13:00:00"
    assert dr.freq == 'h'
    assert dr.resolution == 's'

def test_date_range_range_str_daily_granularity():
    """Test with range_str, daily freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-12-16T14:30:45", freq='D', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-12-16T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 12, 17, 00, 00, 00, tzinfo=timezone.utc) # The last day period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T00:00:00 2024-12-17T00:00:00"
    assert dr.str.full_range_mdy == "03/21/2024T00:00:00 12/17/2024T00:00:00"
    assert dr.str.index_range_ymd == "2024-03-21T00:00:00 2024-12-16T00:00:00"
    assert dr.str.index_range_mdy == "03/21/2024T00:00:00 12/16/2024T00:00:00"
    assert dr.freq == 'D'
    assert dr.resolution == 's'

def test_date_range_range_str_weekly_granularity():
    """Test with range_str, weekly freq, seconds resolution"""
    dr = DateRange(range_str="2020-03-21T14:30:45 2025-06-03T14:30:45", freq='W-SAT', resolution='s')
    assert dr.original_range_str == "2020-03-21T14:30:45 2025-06-03T14:30:45"
    assert dr.start_dt == datetime(2020, 3, 15, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2025, 6, 8, 00, 00, 00, tzinfo=timezone.utc) # The last week period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2020-03-15T00:00:00 2025-06-08T00:00:00"
    assert dr.str.full_range_mdy == "03/15/2020T00:00:00 06/08/2025T00:00:00"
    assert dr.str.index_range_ymd == "2020-03-15T00:00:00 2025-06-01T00:00:00"
    assert dr.str.index_range_mdy == "03/15/2020T00:00:00 06/01/2025T00:00:00"
    assert dr.freq == 'W-SAT'
    assert dr.resolution == 's'

def test_date_range_range_str_monthly_granularity():
    """Test with range_str, monthly freq, seconds resolution"""
    dr = DateRange(range_str="2017-03-21T14:30:45 2023-03-21T14:30:45", freq='M', resolution='s')
    assert dr.original_range_str == "2017-03-21T14:30:45 2023-03-21T14:30:45"
    assert dr.start_dt == datetime(2017, 3, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2023, 4, 1, 00, 00, 00, tzinfo=timezone.utc) # The last month period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2017-03-01T00:00:00 2023-04-01T00:00:00"
    assert dr.str.full_range_mdy == "03/01/2017T00:00:00 04/01/2023T00:00:00"
    assert dr.str.index_range_ymd == "2017-03-01T00:00:00 2023-03-01T00:00:00"
    assert dr.str.index_range_mdy == "03/01/2017T00:00:00 03/01/2023T00:00:00"
    assert dr.freq == 'M'
    assert dr.resolution == 's'



# Now a few spot tests of the output resolutions

def test_date_range_range_str_16minutes_granularity_minute_output_resolution_():
    """Test with range_str, sixteen minutes freq, minutes resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='m')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 13, 42, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-24T13:42"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/24/2024T13:42"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-24T13:26"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/24/2024T13:26"
    assert dr.freq == '16min'
    assert dr.resolution == 'm'

def test_date_range_range_str_16minutes_granularity_hour_output_resolution_():
    """Test with range_str, sixteen minutes freq, hours resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='h')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 13, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03-21T14 2024-03-24T13"
    assert dr.str.full_range_mdy == "03/21/2024T14 03/24/2024T13"
    assert dr.str.index_range_ymd == "2024-03-21T14 2024-03-24T13"
    assert dr.str.index_range_mdy == "03/21/2024T14 03/24/2024T13"
    assert dr.freq == '16min'
    assert dr.resolution == 'h'

def test_date_range_range_str_16minutes_granularity_day_output_resolution_():
    """Test with range_str, sixteen minutes freq, days resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='D')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 00, 00, 00, tzinfo=timezone.utc) 
    assert dr.str.full_range_ymd == "2024-03-21 2024-03-24"
    assert dr.str.full_range_mdy == "03/21/2024 03/24/2024"
    assert dr.str.index_range_ymd == "2024-03-21 2024-03-24"
    assert dr.str.index_range_mdy == "03/21/2024 03/24/2024"
    assert dr.freq == '16min'
    assert dr.resolution == 'D'

def test_date_range_range_str_16minutes_granularity_month_output_resolution_():
    """Test with range_str, sixteen minutes freq, months resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='M')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 1, 00, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024-03 2024-03"
    assert dr.str.full_range_mdy == "03/2024 03/2024"
    assert dr.str.index_range_ymd == "2024-03 2024-03"
    assert dr.str.index_range_mdy == "03/2024 03/2024"
    assert dr.freq == '16min'
    assert dr.resolution == 'M'

def test_date_range_range_str_16minutes_granularity_year_output_resolution_():
    """Test with range_str, sixteen minutes freq, years resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", freq='16min', resolution='Y')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 1, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 1, 1, 00, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.str.full_range_ymd == "2024 2024"
    assert dr.str.full_range_mdy == "2024 2024"
    assert dr.str.index_range_ymd == "2024 2024"
    assert dr.str.index_range_mdy == "2024 2024"
    assert dr.freq == '16min'
    assert dr.resolution == 'Y'





########################################################
# Test GtrendDateRange class
########################################################

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
def test_gdr_range_str_1minutes_granularity():
    """Test with range_str and automatically calculated granularity of 1 minute"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-03-21T18:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-21T18:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 21, 18, 31, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-21T18:31"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/21/2024T18:31"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-21T18:30"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/21/2024T18:30"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-21T18"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/21/2024T18"
    assert dr.granularity == 'm'
    assert dr.freq == 'min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_gdr_range_str_8minutes_granularity():
    """Test with range_str and automatically calculated granularity of 8 minutes"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-03-23T01:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-23T01:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 23, 1, 34, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-23T01:34"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/23/2024T01:34"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-23T01:26"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/23/2024T01:26"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-23T01"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/23/2024T01"
    assert dr.granularity == 'e'
    assert dr.freq == '8min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_gdr_range_str_16minutes_granularity():
    """Test with range_str and automatically calculated granularity of 16 minutes"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 13, 42, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-24T13:42"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/24/2024T13:42"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-24T13:26"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/24/2024T13:26"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-24T13"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/24/2024T13"
    assert dr.granularity == 'n'
    assert dr.freq == '16min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_gdr_range_str_hourly_granularity():
    """Test with range_str and automatically calculated granularity of hourly"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-03-29T13:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-29T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 29, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14 2024-03-29T14"
    assert dr.str.full_range_mdy == "03/21/2024T14 03/29/2024T14"
    assert dr.str.index_range_ymd == "2024-03-21T14 2024-03-29T13"
    assert dr.str.index_range_mdy == "03/21/2024T14 03/29/2024T13"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-29T13"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/29/2024T13"
    assert dr.granularity == 'h'
    assert dr.freq == 'h'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'h'

def test_gdr_range_str_daily_granularity():
    """Test with range_str and automatically calculated granularity of daily"""
    dr = GtrendDateRange(range_str="2024-03-21T14:30:45 2024-12-16T14:30:45")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-12-16T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 12, 17, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21 2024-12-17"
    assert dr.str.full_range_mdy == "03/21/2024 12/17/2024"
    assert dr.str.index_range_ymd == "2024-03-21 2024-12-16"
    assert dr.str.index_range_mdy == "03/21/2024 12/16/2024"
    assert dr.str.search_range_ymd == "2024-03-21 2024-12-16"
    assert dr.str.search_range_mdy == "03/21/2024 12/16/2024"
    assert dr.granularity == 'D'
    assert dr.freq == 'D'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'D'

def test_gdr_range_str_weekly_granularity():
    """Test with range_str and automatically calculated granularity of weekly"""
    dr = GtrendDateRange(range_str="2020-03-21T14:30:45 2025-06-03T14:30:45")
    assert dr.original_range_str == "2020-03-21T14:30:45 2025-06-03T14:30:45"
    assert dr.start_dt == datetime(2020, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2025, 6, 8, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2020-03-15 2025-06-08"
    assert dr.str.full_range_mdy == "03/15/2020 06/08/2025"
    assert dr.str.index_range_ymd == "2020-03-15 2025-06-01"
    assert dr.str.index_range_mdy == "03/15/2020 06/01/2025"
    assert dr.str.search_range_ymd == "2020-03-15 2025-06-01"
    assert dr.str.search_range_mdy == "03/15/2020 06/01/2025"
    assert dr.granularity == 'W'
    assert dr.freq == 'W-SAT'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'D'

def test_gdr_range_str_monthly_granularity():
    """Test with range_str and automatically calculated granularity of monthly"""
    dr = GtrendDateRange(range_str="2017-03-21T14:30:45 2023-03-21T14:30:45")
    assert dr.original_range_str == "2017-03-21T14:30:45 2023-03-21T14:30:45"
    assert dr.start_dt == datetime(2017, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2017-03 2023-04"
    assert dr.str.full_range_mdy == "03/2017 04/2023"
    assert dr.str.index_range_ymd == "2017-03 2023-03"
    assert dr.str.index_range_mdy == "03/2017 03/2023"
    assert dr.str.search_range_ymd == "2017-03-01 2023-03-01"
    assert dr.str.search_range_mdy == "03/01/2017 03/01/2023"
    assert dr.granularity == 'M'
    assert dr.freq == 'M'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'M'



########################################################
# Test SearchSpec class
########################################################

# Test some invalid inputs
def test_search_spec_no_dates():
    """Test creating SearchSpec from no inputs should raise ValueError"""
    with pytest.raises(ValueError):
        SearchSpec()

def test_search_spec_no_dates():
    """Test SearchSpec with freq or resolution should raise ValueError"""
    rs = "2020-03-21 - 2024-03-21"
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, freq='D', search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, resolution='D', search_term="hamburger")

def test_search_spec_invalid_datetime():
    """Test creating SearchSpec from invalid datetime inputs"""
    dt1 = datetime(2024, 3, 21, 14, 30, 45)
    dt2 = datetime(2020, 3, 21, 14, 30, 45) # end date is before start date
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(end=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, end="invalid", search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start="invalid", end=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, end=dt2, search_term="hamburger")

def test_search_spec_invalid_date_str():
    """Test creating SearchSpec from invalid string inputs"""
    dt1 = "2024-03-21"
    dt2 = "2020-03-21" # end date is before start date
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(end=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, end="invalid", search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start="invalid", end=dt1, search_term="hamburger")
    with pytest.raises(ValueError):
        SearchSpec(start=dt1, end=dt2, search_term="hamburger")

def test_search_spec_invalid_range_str():
    """Test creating SearchSpec from invalid range string inputs"""
    rs = "2024-03-21" # only one date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")
    rs = "hamburger - 2025-03-21" # really invalid first date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")
    rs = "2024-03-21 - hotdog" # really invalid second date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")
    rs = "2020-03-61 - 2025-03-21" # invalid first date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")
    rs = "2024-03-21 - 2025-03-61" # invalid second date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")
    rs = "2024-03-21 - 2020-03-21" # first date is after second date
    with pytest.raises(ValueError):
        SearchSpec(range_str=rs, search_term="hamburger")


# Test some inputs with range_str
def test_search_spec_range_str_1minutes_granularity():
    """Test with range_str and automatically calculated granularity of 1 minute"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-03-21T18:30:45", search_term="hamburger")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-21T18:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 21, 18, 31, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-21T18:31"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/21/2024T18:31"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-21T18:30"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/21/2024T18:30"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-21T18"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/21/2024T18"
    assert dr.granularity == 'm'
    assert dr.freq == 'min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_search_spec_range_str_8minutes_granularity():
    """Test with range_str and automatically calculated granularity of 8 minutes"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-03-23T01:30:45", search_term="hamburger")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-23T01:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 23, 1, 34, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-23T01:34"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/23/2024T01:34"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-23T01:26"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/23/2024T01:26"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-23T01"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/23/2024T01"
    assert dr.granularity == 'e'
    assert dr.freq == '8min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_search_spec_range_str_16minutes_granularity():
    """Test with range_str and automatically calculated granularity of 16 minutes"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-03-24T13:30:45", search_term="hamburger")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-24T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 24, 13, 42, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14:30 2024-03-24T13:42"
    assert dr.str.full_range_mdy == "03/21/2024T14:30 03/24/2024T13:42"
    assert dr.str.index_range_ymd == "2024-03-21T14:30 2024-03-24T13:26"
    assert dr.str.index_range_mdy == "03/21/2024T14:30 03/24/2024T13:26"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-24T13"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/24/2024T13"
    assert dr.granularity == 'n'
    assert dr.freq == '16min'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'm'

def test_search_spec_range_str_hourly_granularity():
    """Test with range_str and automatically calculated granularity of hourly"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-03-29T13:30:45", search_term="hamburger"    )
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-29T13:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 29, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21T14 2024-03-29T14"
    assert dr.str.full_range_mdy == "03/21/2024T14 03/29/2024T14"
    assert dr.str.index_range_ymd == "2024-03-21T14 2024-03-29T13"
    assert dr.str.index_range_mdy == "03/21/2024T14 03/29/2024T13"
    assert dr.str.search_range_ymd == "2024-03-21T14 2024-03-29T13"
    assert dr.str.search_range_mdy == "03/21/2024T14 03/29/2024T13"
    assert dr.granularity == 'h'
    assert dr.freq == 'h'
    assert dr.search_resolution == 'h'
    assert dr.resolution == 'h'

def test_search_spec_range_str_daily_granularity():
    """Test with range_str and automatically calculated granularity of daily"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-12-16T14:30:45", search_term="hamburger")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-12-16T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 12, 17, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2024-03-21 2024-12-17"
    assert dr.str.full_range_mdy == "03/21/2024 12/17/2024"
    assert dr.str.index_range_ymd == "2024-03-21 2024-12-16"
    assert dr.str.index_range_mdy == "03/21/2024 12/16/2024"
    assert dr.str.search_range_ymd == "2024-03-21 2024-12-16"
    assert dr.str.search_range_mdy == "03/21/2024 12/16/2024"
    assert dr.granularity == 'D'
    assert dr.freq == 'D'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'D'

def test_search_spec_range_str_weekly_granularity():
    """Test with range_str and automatically calculated granularity of weekly"""
    dr = SearchSpec(range_str="2020-03-21T14:30:45 2025-06-03T14:30:45", search_term="hamburger")
    assert dr.original_range_str == "2020-03-21T14:30:45 2025-06-03T14:30:45"
    assert dr.start_dt == datetime(2020, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2025, 6, 8, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2020-03-15 2025-06-08"
    assert dr.str.full_range_mdy == "03/15/2020 06/08/2025"
    assert dr.str.index_range_ymd == "2020-03-15 2025-06-01"
    assert dr.str.index_range_mdy == "03/15/2020 06/01/2025"
    assert dr.str.search_range_ymd == "2020-03-15 2025-06-01"
    assert dr.str.search_range_mdy == "03/15/2020 06/01/2025"
    assert dr.granularity == 'W'
    assert dr.freq == 'W-SAT'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'D'

def test_search_spec_range_str_monthly_granularity():
    """Test with range_str and automatically calculated granularity of monthly"""
    dr = SearchSpec(range_str="2017-03-21T14:30:45 2023-03-21T14:30:45", search_term="hamburger")
    assert dr.original_range_str == "2017-03-21T14:30:45 2023-03-21T14:30:45"
    assert dr.start_dt == datetime(2017, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.str.full_range_ymd == "2017-03 2023-04"
    assert dr.str.full_range_mdy == "03/2017 04/2023"
    assert dr.str.index_range_ymd == "2017-03 2023-03"
    assert dr.str.index_range_mdy == "03/2017 03/2023"
    assert dr.str.search_range_ymd == "2017-03-01 2023-03-01"
    assert dr.str.search_range_mdy == "03/01/2017 03/01/2023"
    assert dr.granularity == 'M'
    assert dr.freq == 'M'
    assert dr.search_resolution == 'D'
    assert dr.resolution == 'M'
