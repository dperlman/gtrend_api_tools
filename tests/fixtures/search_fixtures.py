"""
Search-related test fixtures for gtrend_api_tools.
"""
import pytest
from datetime import datetime, timezone

@pytest.fixture(scope="module")
def test_terms():
    """Provide common test search terms."""
    return {
        'term1': "hamburger",
        'term2': "pizza",
        'term3': "hot dog",
        'term4': "ice cream",
        'term5': "coffee",
        'term6': "tea",
        'term7': "wine",
        'term8': "beer",
        'term9': "soda",
        'term10': "water"
    }

@pytest.fixture(scope="module")
def multiple_terms():
    """Provide common test search terms with multiple terms."""
    return {
        1: "hot dog",
        2: "coffee,tea",
        3: "breakfast,lunch,dinner",
        4: "bitcoin,ethereum,dogecoin,xrp",
        5: "honda,toyota,ford,chevy,nissan",
        6: "goldfish,clownfish,angelfish,tropical,freshwater,saltwater"
    }

@pytest.fixture(scope="module")
def test_dates():
    """Provide common test date ranges."""
    return {
        'short_range': {
            'start': "2024-01-01",
            'end': "2024-01-30"
        },
        'medium_range': {
            'start': "2024-01-01",
            'end': "2024-05-01"
        },
        'long_range': {
            'start': "2024-01-01",
            'end': "2024-09-01"
        },
        'datetime_range': {
            'start': datetime(2024, 1, 1, tzinfo=timezone.utc),
            'end': datetime(2024, 6, 12, tzinfo=timezone.utc)
        }
    } 

@pytest.fixture(scope="module")
def simple_test_cases():
    return simple_test_case_list

simple_test_case_list = [
    ("2020-01-01 2020-03-01", "breakfast,lunch"),
    ("2020-01-02 2020-03-03", "stock market"),
    ("2020-01-03 2020-03-05", "hot dog,ice cream"),
    ("2020-01-04 2020-03-07", "coffee,tea"),
    ("2020-01-05 2020-03-09", "wine,beer"),
    ("2020-01-06 2020-03-11", "soda,water"),
    ("2020-01-07 2020-03-13", "honda,toyota,ford,chevy,nissan"),
    ("2020-01-08 2020-03-15", "goldfish,clownfish,angelfish"),
    ("2020-01-09 2020-03-17", "freshwater,saltwater"),
    ("2020-01-10 2020-03-19", "bitcoin,ethereum,dogecoin,xrp"),
    ("2020-01-11 2020-03-21", "bacon"),
    ("2020-01-12 2020-03-23", "yogurt,cheese"),
    ("2020-01-13 2020-03-25", "hamburger,pizza"),
    ("2020-01-14 2020-03-27", "therapy"),
    ("2020-01-15 2020-03-29", "election"),
    ("2020-01-16 2020-03-31", "war"),
    ("2020-01-17 2020-04-02", "weather"),
    ("2020-01-18 2020-04-04", "politics"),
    ("2020-01-19 2020-04-06", "economy"),
    ("2020-01-20 2020-04-08", "health"),
    ("2020-01-21 2020-04-10", "crime"),
    ("2020-01-22 2020-04-12", "education"),
    ("2020-01-23 2020-04-14", "technology"),
    ("2020-01-24 2020-04-16", "science"),
    ("2020-01-25 2020-04-18", "environment"),
    ("2020-01-26 2020-04-20", "space"),
    ("2020-01-27 2020-04-22", "sports"),
    ("2020-01-28 2020-04-24", "entertainment"),
    ("2020-01-29 2020-04-26", "travel")
]


@pytest.fixture(scope="module")
def num_granularity_test_dates():
    """Provide the number of granularity test dates."""
    return len(granularity_test_dict)

@pytest.fixture(scope="module")
def granularity_test_dates():
    """Provide comprehensive test date ranges for granularity tests.
    These test cases are verified directly on Google Trends.
    
    Each range tests the boundaries of granularity rules:
    - Max range for each granularity (e.g., 4 hours for one-minute)
    - Next step up to trigger next granularity (e.g., 5 hours for eight-minute)
    """
    return granularity_test_dict

granularity_test_dict = {
    # One-minute granularity tests
    'one_minute_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-01 04:00:00",  # 4 hours - max for one-minute
        'granularity': 'm',
        'expected_rows': 241
    },
    'eight_minute_min': {
        'start': "2020-01-01 00:00:00", 
        'end': "2020-01-01 05:00:00",  # 5 hours - triggers eight-minute
        'granularity': 'e',
        'expected_rows': 38
    },
    
    # Eight-minute granularity tests
    'eight_minute_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-02 11:00:00",  # 35 hours - max for eight-minute
        'granularity': 'e',
        'expected_rows': 263
    },
    'sixteen_minute_min': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-02 12:00:00",  # 36 hours - triggers sixteen-minute
        'granularity': 'n',
        'expected_rows': 136
    },
    
    # Sixteen-minute granularity tests
    'sixteen_minute_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-03 23:00:00",  # 71 hours - max for sixteen-minute
        'granularity': 'n',
        'expected_rows': 267
    },
    'hourly_min': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-04 00:00:00",  # 72 hours - triggers hourly
        'granularity': 'h',
        'expected_rows': 73
    },
    
    # Hourly granularity tests
    # Serpapi was wrong but they fixed it when I reported it. Leaving this here for reference.
    'serpapi_hourly_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-07 23:00:00",  # 6 days 23 hours (167 hours) - max for hourly
        'granularity': 'h',
        'expected_rows': 168 # 167 hours + 1 for including first and last hours
    },
    'hourly_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-08 23:00:00",  # 7 days 23 hours (191 hours) - max for hourly
        'granularity': 'h',
        'expected_rows': 192 # 191 hours + 1 for including first and last hours
    },
    'daily_min': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-01-09 00:00:00",  # 8 days - triggers daily
        'granularity': 'D',
        'expected_rows': 9
    },
    
    # Daily granularity tests
    'daily_max': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-09-26 00:00:00",  # 269 days - max for daily
        'granularity': 'D',
        'expected_rows': 270 # 269 days + 1 for including first and last days
    },
    'weekly_min': {
        'start': "2020-01-01 00:00:00",
        'end': "2020-09-27 00:00:00",  # 271 days - triggers weekly
        'granularity': 'W',
        'expected_rows': 40
    },
    
    # Weekly granularity tests
    'weekly_max': {
        'start': "2017-01-01 00:00:00",
        'end': "2022-03-05 00:00:00",  # 1900 days - triggers monthly
        'granularity': 'W',
        'expected_rows': 270
    },
    'monthly_min': {
        'start': "2017-01-01 00:00:00",
        'end': "2022-03-06 00:00:00",  # 1901 days - triggers monthly
        'granularity': 'M',
        'expected_rows': 63
    },
    
    # Monthly granularity tests (no upper limit)
    'monthly_extended': {
        'start': "2015-01-01 00:00:00",
        'end': "2025-01-01 00:00:00",  # 10 years - well beyond any limit
        'granularity': 'M',
        'expected_rows': 121
    }
} 

@pytest.fixture
def granularity_test_case(request):
    """Fixture that returns individual test cases for parameterization.
    These test cases are verified directly on Google Trends.
    """
    # Convert granularity_test_dict to the expected tuple format
    test_cases = []
    for test_name, test_data in granularity_test_dict.items():
        test_cases.append((
            test_name,
            test_data['start'],
            test_data['end'],
            test_data['granularity'],
            test_data['expected_rows']
        ))
    return test_cases[request.param]


@pytest.fixture
def granularity_transition_case(request):
    """Fixture that returns individual transition test cases for parameterization."""
    transition_cases = [
        ('one_minute_max', 'eight_minute_min', 'm', 'e'),
        ('eight_minute_max', 'sixteen_minute_min', 'e', 'n'),
        ('sixteen_minute_max', 'hourly_min', 'n', 'h'),
        ('hourly_max', 'daily_min', 'h', 'D'),
        ('daily_max', 'weekly_min', 'D', 'W'),
        ('weekly_max', 'monthly_min', 'W', 'M'),
    ]
    return transition_cases[request.param]

@pytest.fixture
def granularity_test_names():
    """Fixture that returns the names of all granularity test cases."""
    return list(granularity_test_dict.keys()) 