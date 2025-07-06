import pytest
import pandas as pd
from datetime import datetime, timedelta
from gtrend_api_tools.granularity import GranularityManager
from gtrend_api_tools.utils import load_config

@pytest.fixture
def granularity_manager(test_config):
    """Fixture providing a GranularityManager instance."""
    return GranularityManager(test_config, verbose=True)

def test_init_with_config(test_config):
    """Test initialization with provided config."""
    gm = GranularityManager(test_config)
    assert isinstance(gm.rules, dict)
    assert len(gm.rules) > 0

def test_init_without_config():
    """Test initialization without config (should raise error)."""
    with pytest.raises(ValueError):
        GranularityManager({})

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

def test_calculate_search_granularity_hourly(granularity_manager):
    """Test search granularity calculation for hourly data."""
    start_date = '2024-01-01'
    end_date = '2024-01-08' # seven days will give hourly granularity
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    len_result_dt_index = len(result['datetime_index'])
    len_result_per_index = len(result['period_index'])
    
    assert result['granularity'] == 'h'
    assert len_result_dt_index == 169  # 7 days *24 hours + 1
    assert len_result_per_index == 169
    assert result['max_units'] == granularity_manager.rules['h']['max_records']


def test_calculate_search_granularity_daily(granularity_manager):
    """Test search granularity calculation for daily data."""
    start_date = '2024-01-01'
    end_date = '2024-01-30'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    
    assert result['granularity'] == 'D'
    assert len(result['datetime_index']) == 30
    assert len(result['period_index']) == 30
    assert result['max_units'] == granularity_manager.rules['D']['max_records']

def test_calculate_search_granularity_automatic_calculation(granularity_manager):
    """Test that search granularity calculation always calculates automatically."""
    start_date = '2024-01-01'
    end_date = '2024-01-30'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    
    # Should automatically calculate appropriate granularity (daily for 30 days)
    assert result['granularity'] == 'D'
    assert len(result['datetime_index']) == 30
    assert len(result['period_index']) == 30
    assert result['max_units'] == granularity_manager.rules['D']['max_records']

def test_calculate_search_granularity_no_granularity_parameter(granularity_manager):
    """Test that search granularity calculation does not accept granularity parameter."""
    start_date = '2024-01-01'
    end_date = '2024-01-02'
    with pytest.raises(TypeError):
        granularity_manager.calculate_search_granularity(start_date, end_date, granularity='D')

def test_calculate_search_granularity_year_long_range(granularity_manager):
    """Test search granularity calculation for a large date range."""
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    result = granularity_manager.calculate_search_granularity(start_date, end_date)
    
    # Should use monthly granularity for a year-long range
    assert result['granularity'] == 'W'
    assert len(result['datetime_index']) == 53  # 52 weeks + 1
    assert len(result['period_index']) == 53
    assert result['max_units'] == granularity_manager.rules['W']['max_records']

def test_calculate_search_granularity_with_datetime_objects(granularity_manager):
    """Test search granularity calculation with datetime objects."""
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2024, 1, 28)
    result = granularity_manager.calculate_search_granularity(start_dt, end_dt)
    
    assert result['granularity'] == 'D'
    assert len(result['datetime_index']) == 28
    assert len(result['period_index']) == 28
    assert result['max_units'] == granularity_manager.rules['D']['max_records']

def test_calculate_search_granularity_with_time_components(granularity_manager):
    """Test search granularity calculation with time components in dates."""
    start_dt = datetime(2024, 1, 1, 12, 30, 45)
    end_dt = datetime(2024, 1, 28, 23, 59, 59)
    result = granularity_manager.calculate_search_granularity(start_dt, end_dt)
    
    # Time components should be truncated
    assert result['granularity'] == 'D'
    assert len(result['datetime_index']) == 28
    assert len(result['period_index']) == 28
    assert result['max_units'] == granularity_manager.rules['D']['max_records']