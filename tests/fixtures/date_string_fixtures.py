"""
Search-related test fixtures for gtrend_api_tools.
"""
import pytest
from datetime import datetime, timezone

@pytest.fixture(scope="module")
def test_first_date_strings():
    """Some of the kinds of date strings that are returned by different APIs.
    Structure is (input_date_string, expected_parsed_date)
    Note that some of these intentionally have weird Unicode spaces and other characters."""
    return [
        ("Dec 29, 2019 - Jan 4, 2020", "2019-12-29T00:00:00"),
        ("Dec 31, 2017 - Jan 6, 2018", "2017-12-31T00:00:00"),
        ("Dec 29, 2019 - Jan 4, 2020", "2019-12-29T00:00:00"),
        ("2020-01-01", "2020-01-01T00:00:00"),
        ("2020-01-01 00:00:00", "2020-01-01T00:00:00"),
        ("2020-01-01T00 2020-01-01T04", "2020-01-01T00:00:00"),
        ("Jan 1, 2020 at 12:02 AM", "2020-01-01T00:02:00"),
        ("Jan 1, 2020 at 12:02 AM", "2020-01-01T00:02:00"),
        ("Jan 1, 2020", "2020-01-01T00:00:00"),
        ("12/31/19, 5:00 PM - 1/7/20, 4:00 PM", "2019-12-31T17:00:00")
    ]



