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
    assert dr.formatted_range_ymd == "2024-03-21T00 2024-03-29T00"
    assert dr.formatted_range_mdy == "03/21/2024T00 03/29/2024T00"
    assert dr.freq == 'D'
    assert dr.resolution == 'h'



# Now a whole series to try all the different freqs and resolutions

def test_date_range_range_str_minutes_freq():
    """Test with range_str, minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 14, 31, 00, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2024-03-21T14:30:00 2024-03-28T14:31:00"
    assert dr.formatted_range_mdy == "03/21/2024T14:30:00 03/28/2024T14:31:00"
    assert dr.freq == 'min'
    assert dr.resolution == 's'

def test_date_range_range_str_8minutes_freq():
    """Test with range_str, 8 minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='8min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 14, 38, 00, tzinfo=timezone.utc) # The last 8min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T14:30:00 2024-03-28T14:38:00"
    assert dr.formatted_range_mdy == "03/21/2024T14:30:00 03/28/2024T14:38:00"
    assert dr.freq == '8min'
    assert dr.resolution == 's'

def test_date_range_range_str_16minutes_granularity():
    """Test with range_str, sixteen minutes freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 14, 46, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T14:30:00 2024-03-28T14:46:00"
    assert dr.formatted_range_mdy == "03/21/2024T14:30:00 03/28/2024T14:46:00"
    assert dr.freq == '16min'
    assert dr.resolution == 's'

def test_date_range_range_str_hourly_granularity():
    """Test with range_str, hourly freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='h', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 15, 00, 00, tzinfo=timezone.utc) # The last hour period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T14:00:00 2024-03-28T15:00:00"
    assert dr.formatted_range_mdy == "03/21/2024T14:00:00 03/28/2024T15:00:00"
    assert dr.freq == 'h'
    assert dr.resolution == 's'

def test_date_range_range_str_daily_granularity():
    """Test with range_str, daily freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='D', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 29, 00, 00, 00, tzinfo=timezone.utc) # The last day period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T00:00:00 2024-03-29T00:00:00"
    assert dr.formatted_range_mdy == "03/21/2024T00:00:00 03/29/2024T00:00:00"
    assert dr.freq == 'D'
    assert dr.resolution == 's'

def test_date_range_range_str_weekly_granularity():
    """Test with range_str, weekly freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2025-03-28T14:30:45", freq='W-SAT', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2025-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 17, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2025, 3, 30, 00, 00, 00, tzinfo=timezone.utc) # The last week period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-17T00:00:00 2025-03-30T00:00:00"
    assert dr.formatted_range_mdy == "03/17/2024T00:00:00 03/30/2025T00:00:00"
    assert dr.freq == 'W-SAT'
    assert dr.resolution == 's'

def test_date_range_range_str_monthly_granularity():
    """Test with range_str, monthly freq, seconds resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2025-03-28T14:30:45", freq='M', resolution='s')
    assert dr.original_range_str == "2024-03-21T14:30:45 2025-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2025, 4, 1, 00, 00, 00, tzinfo=timezone.utc) # The last month period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-01T00:00:00 2025-04-01T00:00:00"
    assert dr.formatted_range_mdy == "03/01/2024T00:00:00 04/01/2025T00:00:00"
    assert dr.freq == 'M'
    assert dr.resolution == 's'



# Now a few spot tests of the output resolutions

def test_date_range_range_str_16minutes_granularity_minute_output_resolution_():
    """Test with range_str, sixteen minutes freq, minutes resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='m')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 14, 46, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T14:30 2024-03-28T14:46"
    assert dr.formatted_range_mdy == "03/21/2024T14:30 03/28/2024T14:46"
    assert dr.freq == '16min'
    assert dr.resolution == 'm'

def test_date_range_range_str_16minutes_granularity_hour_output_resolution_():
    """Test with range_str, sixteen minutes freq, hours resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='h')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 14, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21T14 2024-03-28T14"
    assert dr.formatted_range_mdy == "03/21/2024T14 03/28/2024T14"
    assert dr.freq == '16min'
    assert dr.resolution == 'h'

def test_date_range_range_str_16minutes_granularity_day_output_resolution_():
    """Test with range_str, sixteen minutes freq, days resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='D')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 00, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03-21 2024-03-28"
    assert dr.formatted_range_mdy == "03/21/2024 03/28/2024"
    assert dr.freq == '16min'
    assert dr.resolution == 'D'

def test_date_range_range_str_16minutes_granularity_month_output_resolution_():
    """Test with range_str, sixteen minutes freq, months resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='M')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 1, 00, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024-03 2024-03"
    assert dr.formatted_range_mdy == "03/2024 03/2024"
    assert dr.freq == '16min'
    assert dr.resolution == 'M'

def test_date_range_range_str_16minutes_granularity_year_output_resolution_():
    """Test with range_str, sixteen minutes freq, years resolution"""
    dr = DateRange(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", freq='16min', resolution='Y')
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 1, 1, 00, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 1, 1, 00, 00, 00, tzinfo=timezone.utc) # The last 16min period will include the given end time. Then, this end_dt is the end of that period.
    assert dr.formatted_range_ymd == "2024 2024"
    assert dr.formatted_range_mdy == "2024 2024"
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
def test_search_spec_range_str_hourly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    dr = SearchSpec(range_str="2024-03-21T14:30:45 2024-03-28T14:30:45", search_term="hamburger")
    assert dr.original_range_str == "2024-03-21T14:30:45 2024-03-28T14:30:45"
    assert dr.start_dt == datetime(2024, 3, 21, 14, 00, 00, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 3, 28, 15, 00, 00, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2024-03-21T14 2024-03-28T15"
    assert dr.formatted_range_mdy == "03/21/2024T14 03/28/2024T15"
    assert dr.granularity == 'h'
    assert dr.freq == 'h'
    assert dr.resolution == 'h'

def test_search_spec_range_str_daily_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match daily granularity: 2024-03-01 2024-03-28
    dr = SearchSpec(range_str="2024-03-01 2024-09-28", search_term="hamburger")
    assert dr.original_range_str == "2024-03-01 2024-09-28"
    assert dr.start_dt == datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 9, 29, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2024-03-01 2024-09-29"
    assert dr.formatted_range_mdy == "03/01/2024 09/29/2024"
    assert dr.granularity == 'D'
    assert dr.freq == 'D'
    assert dr.resolution == 'D'

def test_search_spec_range_str_weekly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match weekly granularity: 2024-01-07 2024-03-31 (Sundays)
    dr = SearchSpec(range_str="2020-01-07 2024-03-31", search_term="hamburger")
    assert dr.original_range_str == "2020-01-07 2024-03-31"
    assert dr.start_dt == datetime(2020, 1, 5, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 4, 7, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2020-01-05 2024-04-07"
    assert dr.formatted_range_mdy == "01/05/2020 04/07/2024"
    assert dr.granularity == 'W'
    assert dr.freq == 'W-SAT'
    assert dr.resolution == 'D'

def test_search_spec_range_str_monthly_granularity():
    """Test with range_str and automatically calculated granularity (as always)"""
    # Changed input to match monthly granularity: 2023-01 2024-03
    dr = SearchSpec(range_str="2017-01-07 2024-03-31", search_term="hamburger")
    assert dr.original_range_str == "2017-01-07 2024-03-31"
    assert dr.start_dt == datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.end_dt == datetime(2024, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert dr.formatted_range_ymd == "2017-01 2024-04"
    assert dr.formatted_range_mdy == "01/2017 04/2024"
    assert dr.granularity == 'M'
    assert dr.freq == 'M'
    assert dr.resolution == 'M'

























# # Test some inputs with pair of datetimes
# def test_date_range_dt_pair():
#     """Test with pair of datetimes and default granularity"""
#     print("Running test: Pair of datetimes")
#     start = datetime(2024, 3, 21, 14, 30, 45)
#     end = datetime(2024, 3, 28, 14, 30, 45)
#     range_space = " "
#     dr = DateRange(start_date=start, end_date=end, range_space=range_space)
#     assert dr.start_dt == start.replace(hour=0, minute=0, second=0, microsecond=0)
#     assert dr.end_dt == end.replace(hour=0, minute=0, second=0, microsecond=0)
#     assert dr.formatted_range_ymd == "2024-03-21 2024-03-28"
#     assert dr.formatted_range_mdy == "03/21/2024 03/28/2024"
#     assert dr.granularity == 'D'
#     #print("PASSED: Pair of datetimes")




# def test_make_time_range_granularity_seconds():
#     """Test make_time_range with seconds granularity"""
#     print("Running test: Seconds granularity")
#     dr = DateRange()
#     dr.granularity = 's'
    
#     start = datetime(2024, 3, 21, 14, 30, 45, 123456)
#     end = datetime(2024, 3, 21, 14, 30, 46, 789012)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 3, 21, 14, 30, 45)
#     assert dr.end_dt == datetime(2024, 3, 21, 14, 30, 46)
#     assert dr.formatted_start_date_ymd == "2024-03-21T14:30:45"
#     assert dr.formatted_start_date_mdy == "03/21/2024T14:30:45"
#     assert dr.formatted_end_date_ymd == "2024-03-21T14:30:46"
#     assert dr.formatted_end_date_mdy == "03/21/2024T14:30:46"
#     #print("PASSED: Seconds granularity")

# def test_make_time_range_granularity_minutes():
#     """Test make_time_range with minutes granularity"""
#     print("Running test: Minutes granularity")
#     dr = DateRange()
#     dr.granularity = 'm'
    
#     start = datetime(2024, 3, 21, 14, 30, 45)
#     end = datetime(2024, 3, 21, 14, 31, 15)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 3, 21, 14, 30)
#     assert dr.end_dt == datetime(2024, 3, 21, 14, 31)
#     assert dr.formatted_start_date_ymd == "2024-03-21T14:30"
#     assert dr.formatted_start_date_mdy == "03/21/2024T14:30"
#     assert dr.formatted_end_date_ymd == "2024-03-21T14:31"
#     assert dr.formatted_end_date_mdy == "03/21/2024T14:31"
#     #print("PASSED: Minutes granularity")

# def test_make_time_range_granularity_hours():
#     """Test make_time_range with hours granularity"""
#     print("Running test: Hours granularity")
#     dr = DateRange()
#     dr.granularity = 'h'
    
#     start = datetime(2024, 3, 21, 14, 30, 45)
#     end = datetime(2024, 3, 21, 15, 20, 30)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 3, 21, 14)
#     assert dr.end_dt == datetime(2024, 3, 21, 15)
#     assert dr.formatted_start_date_ymd == "2024-03-21T14"
#     assert dr.formatted_start_date_mdy == "03/21/2024T14"
#     assert dr.formatted_end_date_ymd == "2024-03-21T15"
#     assert dr.formatted_end_date_mdy == "03/21/2024T15"
#     #print("PASSED: Hours granularity")

# def test_make_time_range_granularity_days():
#     """Test make_time_range with days granularity"""
#     print("Running test: Days granularity")
#     dr = DateRange()
#     dr.granularity = 'D'
    
#     start = datetime(2024, 3, 21, 14, 30, 45)
#     end = datetime(2024, 3, 22, 15, 20, 30)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 3, 21)
#     assert dr.end_dt == datetime(2024, 3, 22)
#     assert dr.formatted_start_date_ymd == "2024-03-21"
#     assert dr.formatted_start_date_mdy == "03/21/2024"
#     assert dr.formatted_end_date_ymd == "2024-03-22"
#     assert dr.formatted_end_date_mdy == "03/22/2024"
#     #print("PASSED: Days granularity")

# def test_make_time_range_granularity_weeks():
#     """Test make_time_range with weeks granularity"""
#     print("Running test: Weeks granularity")
#     dr = DateRange()
#     dr.granularity = 'W'
    
#     # Wednesday to Tuesday
#     start = datetime(2024, 3, 20, 14, 30, 45)  # Wednesday
#     end = datetime(2024, 3, 26, 15, 20, 30)    # Tuesday
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     # Should round to previous Sunday and next Saturday
#     assert dr.start_dt == datetime(2024, 3, 17)  # Sunday
#     assert dr.end_dt == datetime(2024, 3, 30)  # Saturday
#     assert dr.formatted_start_date_ymd == "2024-03-17"
#     assert dr.formatted_start_date_mdy == "03/17/2024"
#     assert dr.formatted_end_date_ymd == "2024-03-30"
#     assert dr.formatted_end_date_mdy == "03/30/2024"
#     #print("PASSED: Weeks granularity")

# def test_make_time_range_granularity_months():
#     """Test make_time_range with months granularity"""
#     print("Running test: Months granularity")
#     dr = DateRange()
#     dr.granularity = 'M'
    
#     start = datetime(2024, 3, 15, 14, 30, 45)
#     end = datetime(2024, 3, 20, 15, 20, 30)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 3, 1)
#     assert dr.end_dt == datetime(2024, 3, 31)
#     assert dr.formatted_start_date_ymd == "2024-03-01"
#     assert dr.formatted_start_date_mdy == "03/01/2024"
#     assert dr.formatted_end_date_ymd == "2024-03-31"
#     assert dr.formatted_end_date_mdy == "03/31/2024"
#     #print("PASSED: Months granularity")

# def test_make_time_range_granularity_quarters():
#     """Test make_time_range with quarters granularity"""
#     print("Running test: Quarters granularity")
#     dr = DateRange()
#     dr.granularity = 'Q'
    
#     start = datetime(2024, 2, 15, 14, 30, 45)  # Q1
#     end = datetime(2024, 5, 20, 15, 20, 30)    # Q2
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 1, 1)   # Start of Q1
#     assert dr.end_dt == datetime(2024, 6, 30)  # End of Q2
#     assert dr.formatted_start_date_ymd == "2024-01-01"
#     assert dr.formatted_start_date_mdy == "01/01/2024"
#     assert dr.formatted_end_date_ymd == "2024-06-30"
#     assert dr.formatted_end_date_mdy == "06/30/2024"
#     #print("PASSED: Quarters granularity")

# def test_make_time_range_granularity_years():
#     """Test make_time_range with years granularity"""
#     print("Running test: Years granularity")
#     dr = DateRange()
#     dr.granularity = 'Y'
    
#     start = datetime(2024, 3, 15, 14, 30, 45)
#     end = datetime(2024, 8, 20, 15, 20, 30)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2024, 1, 1)
#     assert dr.end_dt == datetime(2024, 12, 31)
#     assert dr.formatted_start_date_ymd == "2024-01-01"
#     assert dr.formatted_start_date_mdy == "01/01/2024"
#     assert dr.formatted_end_date_ymd == "2024-12-31"
#     assert dr.formatted_end_date_mdy == "12/31/2024"
#     #print("PASSED: Years granularity")

# def test_make_time_range_granularity_decades():
#     """Test make_time_range with decades granularity"""
#     print("Running test: Decades granularity")
#     dr = DateRange()
#     dr.granularity = 'X'
    
#     start = datetime(2024, 3, 15, 14, 30, 45)
#     end = datetime(2028, 8, 20, 15, 20, 30)
    
#     dr.make_time_range(start, end)
    
#     assert dr.original_date_str is None  # Not set by make_time_range
#     assert dr.start_dt == datetime(2020, 1, 1)
#     assert dr.end_dt == datetime(2029, 12, 31)
#     assert dr.formatted_start_date_ymd == "2020-01-01"
#     assert dr.formatted_start_date_mdy == "01/01/2020"
#     assert dr.formatted_end_date_ymd == "2029-12-31"
#     assert dr.formatted_end_date_mdy == "12/31/2029"
#     #print("PASSED: Decades granularity")

# def test_make_time_range_invalid_granularity():
#     """Test make_time_range with invalid granularity"""
#     print("Running test: Invalid granularity")
#     dr = DateRange()
#     dr.granularity = 'invalid'
    
#     with pytest.raises(ValueError, match="Invalid granularity"):
#         dr.make_time_range(datetime.now())
#     #print("PASSED: Invalid granularity")

# def test_make_time_range_string_dates():
#     """Test make_time_range with string dates"""
#     print("Running test: String dates")
#     dr = DateRange()
    
#     dr.make_time_range("2024-03-21", "2024-03-28")
    
#     assert dr.start_dt == datetime(2024, 3, 21)
#     assert dr.end_dt == datetime(2024, 3, 28)
#     #print("PASSED: String dates")

# def test_make_time_range_method_chaining():
#     """Test make_time_range method chaining"""
#     print("Running test: Method chaining")
#     dr = DateRange()
#     result = dr.make_time_range(datetime(2024, 3, 21))
    
#     assert result is dr
#     assert dr.formatted_range_ymd == "2024-03-21"
#     assert dr.formatted_range_mdy == "03/21/2024"
#     #print("PASSED: Method chaining")

# def test_standardize_date_str():
#     """Test date string standardization"""
#     print("Running test: Date string standardization")
#     dr = DateRange()
#     dr._init_from_str("Mar 21 - 28, 2024")
    
#     assert dr.start_dt == datetime(2024, 3, 21)
#     assert dr.end_dt == datetime(2024, 3, 28)
#     assert dr.start_incomplete is False
#     assert dr.end_incomplete is False
#     assert dr.formatted_range_ymd == "2024-03-21 2024-03-28"
#     assert dr.formatted_range_mdy == "03/21/2024 03/28/2024"
#     #print("PASSED: Date string standardization")

# def test_standardize_date_str_single_date():
#     """Test date string standardization with single date"""
#     print("Running test: Single date string")
#     dr = DateRange()
#     dr._init_from_str("Mar 21, 2024")
    
#     assert dr.start_dt == datetime(2024, 3, 21)
#     assert dr.end_dt is None
#     assert dr.start_incomplete is False
#     assert dr.end_incomplete is True
#     assert dr.formatted_range_ymd == "2024-03-21"
#     assert dr.formatted_range_mdy == "03/21/2024"
#     #print("PASSED: Single date string")

# def test_standardize_date_str_invalid():
#     """Test date string standardization with invalid input"""
#     print("Running test: Invalid date string")
#     dr = DateRange()
#     with pytest.raises(ValueError):
#         dr._init_from_str("invalid date")
#     #print("PASSED: Invalid date string")

# def test_from_str_granularity():
#     """Test from_str with different granularities"""
#     print("Running test: from_str granularity")
    
#     # Test daily granularity (default)
#     dr = DateRange.from_str("2024-03-21")
#     assert dr.granularity == 'D'
#     assert dr.start_dt.hour == 0
#     assert dr.start_dt.minute == 0
#     assert dr.start_dt.second == 0
    
#     # Test hourly granularity
#     dr = DateRange.from_str("2024-03-21", granularity='hourly')
#     assert dr.granularity == 'h'
#     assert dr.start_dt.hour == 0  # Still 0 because we don't have time in the string
    
#     # Test minute granularity
#     dr = DateRange.from_str("2024-03-21", granularity='minute')
#     assert dr.granularity == 'm'
#     assert dr.start_dt.minute == 0  # Still 0 because we don't have time in the string
    
#     #print("PASSED: from_str granularity")

# def test_from_dt_granularity():
#     """Test from_dt with different granularities"""
#     print("Running test: from_dt granularity")
    
#     # Test daily granularity (default)
#     dt = datetime(2024, 3, 21, 14, 30, 45)
#     dr = DateRange.from_dt(dt)
#     assert dr.granularity == 'D'
#     assert dr.start_dt.hour == 0
#     assert dr.start_dt.minute == 0
#     assert dr.start_dt.second == 0
    
#     # Test hourly granularity
#     dr = DateRange.from_dt(dt, granularity='hourly')
#     assert dr.granularity == 'h'
#     assert dr.start_dt.hour == 14
#     assert dr.start_dt.minute == 0
#     assert dr.start_dt.second == 0
    
#     # Test minute granularity
#     dr = DateRange.from_dt(dt, granularity='minute')
#     assert dr.granularity == 'm'
#     assert dr.start_dt.hour == 14
#     assert dr.start_dt.minute == 30
#     assert dr.start_dt.second == 0
    
#     # Test second granularity
#     dr = DateRange.from_dt(dt, granularity='second')
#     assert dr.granularity == 's'
#     assert dr.start_dt.hour == 14
#     assert dr.start_dt.minute == 30
#     assert dr.start_dt.second == 45
    
#     #print("PASSED: from_dt granularity")