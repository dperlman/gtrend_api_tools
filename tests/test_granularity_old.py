import pytest
import pandas as pd
from datetime import datetime, timedelta
from gtrend_api_tools.granularity import GranularityManager
from gtrend_api_tools.utils import load_config

@pytest.fixture
def granularity_manager(test_config):
    """Fixture providing a GranularityManager instance."""
    return GranularityManager(test_config)

def test_init_with_config(test_config):
    """Test initialization with provided config."""
    gm = GranularityManager(test_config)
    assert isinstance(gm.rules, dict)
    assert len(gm.rules) > 0

def test_init_without_config():
    """Test initialization without config (should raise error)."""
    with pytest.raises(ValueError):
        GranularityManager({})


def test_create_time_indices_hourly(granularity_manager):
    """Test time index creation for hourly data."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 1, 23, 0, 0)
    dt_index, period_index = granularity_manager.create_time_indices(start_dt, end_dt, 'h')
    
    assert len(dt_index) == 24
    assert len(period_index) == 24
    assert dt_index.freqstr == 'h'
    assert period_index.freqstr == 'h'

def test_create_time_indices_daily(granularity_manager):
    """Test time index creation for daily data."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 7)
    dt_index, period_index = granularity_manager.create_time_indices(start_dt, end_dt, 'D')
    
    assert len(dt_index) == 7
    assert len(period_index) == 7
    assert dt_index.freqstr == 'D'
    assert period_index.freqstr == 'D'

def test_create_time_indices_invalid_granularity(granularity_manager):
    """Test time index creation with invalid granularity."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 2)
    with pytest.raises(ValueError):
        granularity_manager.create_time_indices(start_dt, end_dt, 'X')

def test_calculate_total_units_hourly(granularity_manager):
    """Test total units calculation for hourly data."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 1, 23, 0, 0)
    assert granularity_manager.calculate_total_units(start_dt, end_dt, 'h')['num_periods'] == 24

def test_calculate_total_units_daily(granularity_manager):
    """Test total units calculation for daily data."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 7)
    assert granularity_manager.calculate_total_units(start_dt, end_dt, 'D')['num_periods'] == 7

def test_calculate_total_units_invalid_granularity(granularity_manager):
    """Test total units calculation with invalid granularity."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 2)
    with pytest.raises(ValueError):
        granularity_manager.calculate_total_units(start_dt, end_dt, 'X')


# Tests for granularity detection

def test_get_index_granularity_hourly(granularity_manager):
    """Test granularity detection for hourly data."""
    # Create hourly index
    index = pd.date_range(start='2024-01-01', periods=24, freq='h')
    assert granularity_manager.get_index_granularity(index) == 'h'

def test_get_index_granularity_daily(granularity_manager):
    """Test granularity detection for daily data."""
    # Create daily index
    index = pd.date_range(start='2024-01-01', periods=7, freq='D')
    assert granularity_manager.get_index_granularity(index) == 'D'

def test_get_index_granularity_weekly(granularity_manager):
    """Test granularity detection for weekly data."""
    # Create weekly index
    index = pd.date_range(start='2024-01-01', periods=4, freq='W')
    assert granularity_manager.get_index_granularity(index) == 'W'

def test_get_index_granularity_monthly(granularity_manager):
    """Test granularity detection for monthly data."""
    # Create monthly index
    index = pd.date_range(start='2024-01-01', periods=12, freq='MS')
    assert granularity_manager.get_index_granularity(index) == 'M'

def test_get_index_granularity_empty(granularity_manager):
    """Test granularity detection with empty index."""
    index = pd.DatetimeIndex([])
    assert granularity_manager.get_index_granularity(index) is None

def test_get_index_granularity_single_point(granularity_manager):
    """Test granularity detection with single data point."""
    index = pd.DatetimeIndex(['2024-01-01'])
    assert granularity_manager.get_index_granularity(index) is None



# Tests for general features of search granularity calculation

def test_calculate_search_granularity_no_granularity_parameter(granularity_manager):
    """Test that search granularity calculation does not accept granularity parameter."""
    start_date = '2024-01-01'
    end_date = '2024-01-02'
    with pytest.raises(TypeError):
        granularity_manager.calculate_search_granularity(start_date, end_date, granularity='D')

def test_calculate_search_granularity_with_datetime_objects(granularity_manager):
    """Test search granularity calculation with datetime objects."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 28)
    result = granularity_manager.calculate_search_granularity(start_dt, end_dt)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    assert result['granularity'] == 'D'
    assert len_result_dt_index == 28
    assert len_result_per_index == 28
    assert result['max_units'] == granularity_manager.rules['D']['max_records']

def test_calculate_search_granularity_with_time_components(granularity_manager):
    """Test search granularity calculation with time components in dates."""
    start_dt = datetime(2024, 1, 1, 12, 30, 45)
    end_dt = datetime(2024, 1, 28, 23, 59, 59)
    result = granularity_manager.calculate_search_granularity(start_dt, end_dt)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # Time components should be truncated
    assert result['granularity'] == 'D'
    assert len_result_dt_index == 28
    assert len_result_per_index == 28
    assert result['max_units'] == granularity_manager.rules['D']['max_records']



# # Here is the comprehensive set of tests for all granularities

def test_calculate_search_granularity_monthly(granularity_manager):
    """Test search granularity calculation for a date range that should give monthly granularity."""
    start_date = '2020-01-01'
    end_date = '2026-01-01'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # six year range should give monthly granularity
    assert result['granularity'] == 'M'
    assert len_result_dt_index == 73  # I trust this is the right number of months but I kinda didn't work through it in detail
    assert len_result_per_index == 73
    assert result['max_units'] == granularity_manager.rules['M']['max_records']

def test_calculate_search_granularity_weekly(granularity_manager):
    """Test search granularity calculation for a date range that should give weekly granularity."""
    start_date = '2020-01-01'
    end_date = '2025-01-01'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    #print(result['period_index'])
    #print(result['datetime_index'])
    # five year range should give weekly granularity
    assert result['granularity'] == 'W'
    assert len_result_dt_index == 262  # timedelta of given range is 261 days, so 262 periods
    assert len_result_per_index == 262
    assert result['max_units'] == granularity_manager.rules['W']['max_records']

def test_calculate_search_granularity_daily(granularity_manager):
    """Test search granularity calculation for a date range that should give daily granularity."""
    start_date = '2020-01-01'
    end_date = '2020-06-01'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # six month range should give daily granularity
    assert result['granularity'] == 'D'
    assert len_result_dt_index == 153  # timedelta of given range is 152 days, so 153 periods
    assert len_result_per_index == 153
    assert result['max_units'] == granularity_manager.rules['D']['max_records']

def test_calculate_search_granularity_hourly(granularity_manager):
    """Test search granularity calculation for a date range that should give hourly granularity."""
    start_date = '2020-01-01'
    end_date = '2020-01-07'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # seven day range should give hourly granularity
    assert result['granularity'] == 'h'
    assert len_result_dt_index == 145  # timedelta of given range is 518400 seconds, 144 hours, so 145 periods
    assert len_result_per_index == 145
    assert result['max_units'] == granularity_manager.rules['h']['max_records']

def test_calculate_search_granularity_sixteen_minute(granularity_manager):
    """Test search granularity calculation for a date range that should give sixteen minute granularity."""
    start_date = '2020-01-01'
    end_date = '2020-01-03'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # two day range should give sixteen minute granularity
    assert result['granularity'] == 'n'
    assert len_result_dt_index == 181  # 
    assert len_result_per_index == 181
    assert result['max_units'] == granularity_manager.rules['n']['max_records']

def test_calculate_search_granularity_eight_minute(granularity_manager):
    """Test search granularity calculation for a date range that should give eight minute granularity."""
    start_date = '2020-01-01'
    end_date = '2020-01-02'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # one day range should give eight minute granularity
    assert result['granularity'] == 'e'
    assert len_result_dt_index == 181  # 24 hours in minutes is 1440, divided by 8 is 180, so 181 periods
    assert len_result_per_index == 181
    assert result['max_units'] == granularity_manager.rules['e']['max_records']

def test_calculate_search_granularity_one_minute(granularity_manager):
    """Test search granularity calculation for a date range that should give one minute granularity."""
    start_date = '2020-01-01 00:00:00'
    end_date = '2020-01-01 04:00:00'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    # four hour range should give one minute granularity
    assert result['granularity'] == 'm'
    assert len_result_dt_index == 241  # 4 hours in minutes is 240 minutes, so 241 periods
    assert len_result_per_index == 241
    assert result['max_units'] == granularity_manager.rules['m']['max_records']
