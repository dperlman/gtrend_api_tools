import pytest
from gtrend_api_tools.date_strings import split_date_range_str, cleanup_date_str


class TestSplitDateRangeStr:
    """Test cases for split_date_range_str function based on patterns in the function comments."""
    
    def test_iso_datetime_with_space_separator(self):
        """Test ISO datetime format with space separator."""
        # 2020-01-01T14:30:45 2020-01-07T14:30:45
        date_str = "2020-01-01T14:30:45 2020-01-07T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14:30:45"
        assert end_date == "2020-01-07T14:30:45"
    
    def test_iso_datetime_with_minutes_only(self):
        """Test ISO datetime format with minutes only."""
        # 2020-01-01T14:30 2020-01-07T14:30
        date_str = "2020-01-01T14:30 2020-01-07T14:30"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14:30"
        assert end_date == "2020-01-07T14:30"
    
    def test_iso_datetime_with_hours_only(self):
        """Test ISO datetime format with hours only."""
        # 2020-01-01T14 2020-01-07T14
        date_str = "2020-01-01T14 2020-01-07T14"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14"
        assert end_date == "2020-01-07T14"
    
    def test_iso_datetime_with_dash_separator(self):
        """Test ISO datetime format with dash separator."""
        # 2020-01-01T14:30:45 - 2020-01-07T14:30:45
        date_str = "2020-01-01T14:30:45 - 2020-01-07T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14:30:45"
        assert end_date == "2020-01-07T14:30:45"
    
    def test_iso_datetime_with_multiple_spaces_around_dash(self):
        """Test ISO datetime format with multiple spaces around dash."""
        # 2020-01-01T14:30:45  -  2020-01-07T14:30:45
        date_str = "2020-01-01T14:30:45  -  2020-01-07T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14:30:45"
        assert end_date == "2020-01-07T14:30:45"
    
    def test_mdy_datetime_with_space_separator(self):
        """Test MDY datetime format with space separator."""
        # 01/01/2020T14:30:45 01/07/2020T14:30:45
        date_str = "01/01/2020T14:30:45 01/07/2020T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "01/01/2020T14:30:45"
        assert end_date == "01/07/2020T14:30:45"
    
    def test_mdy_datetime_with_dash_separator(self):
        """Test MDY datetime format with dash separator."""
        # 01/01/2020T14:30:45 - 01/07/2020T14:30:45
        date_str = "01/01/2020T14:30:45 - 01/07/2020T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "01/01/2020T14:30:45"
        assert end_date == "01/07/2020T14:30:45"
    
    def test_mdy_datetime_with_minutes_only(self):
        """Test MDY datetime format with minutes only."""
        # 01/01/2020T14:30 01/07/2020T14:30
        date_str = "01/01/2020T14:30 01/07/2020T14:30"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "01/01/2020T14:30"
        assert end_date == "01/07/2020T14:30"
    
    def test_iso_date_with_dash_separator(self):
        """Test ISO date format with dash separator."""
        # 2020-01-01 - 2020-01-07
        date_str = "2020-01-01 - 2020-01-07"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01"
        assert end_date == "2020-01-07"
    
    def test_iso_date_with_space_separator(self):
        """Test ISO date format with space separator."""
        # 2020-01-01 2020-01-07
        date_str = "2020-01-01 2020-01-07"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01"
        assert end_date == "2020-01-07"
    
    def test_iso_date_with_multiple_spaces_around_dash(self):
        """Test ISO date format with multiple spaces around dash."""
        # 2020-01-01  -  2020-01-07
        date_str = "2020-01-01  -  2020-01-07"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01"
        assert end_date == "2020-01-07"
    
    def test_mdy_date_with_dash_separator(self):
        """Test MDY date format with dash separator."""
        # 11/3/2021 - 11/10/2021
        date_str = "11/3/2021 - 11/10/2021"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "11/3/2021"
        assert end_date == "11/10/2021"
    
    def test_mdy_date_with_space_separator(self):
        """Test MDY date format with space separator."""
        # 11/3/2021 11/10/2021
        date_str = "11/3/2021 11/10/2021"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "11/3/2021"
        assert end_date == "11/10/2021"
    
    def test_mdy_date_with_multiple_spaces_around_dash(self):
        """Test MDY date format with multiple spaces around dash."""
        # 11/3/2021  -  11/10/2021
        date_str = "11/3/2021  -  11/10/2021"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "11/3/2021"
        assert end_date == "11/10/2021"
    
    def test_month_day_range_no_spaces_around_dash(self):
        """Test month day range with no spaces around dash."""
        # Jan 1-7, 2020
        date_str = "Jan 1-7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Jan 7, 2020"
    
    def test_month_day_range_no_comma(self):
        """Test month day range without comma."""
        # Jan 1-7 2020
        date_str = "Jan 1-7 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Jan 7, 2020"
    
    def test_month_day_range_with_spaces_around_dash(self):
        """Test month day range with spaces around dash."""
        # Jan 1 - 7, 2020
        date_str = "Jan 1 - 7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Jan 7, 2020"
    
    def test_month_day_range_with_multiple_spaces_around_dash(self):
        """Test month day range with multiple spaces around dash."""
        # Jan 1  -  7, 2020
        date_str = "Jan 1  -  7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Jan 7, 2020"
    
    def test_month_day_range_no_comma_with_spaces(self):
        """Test month day range without comma but with spaces around dash."""
        # Jan 1 - 7 2020
        date_str = "Jan 1 - 7 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Jan 7, 2020"
    
    def test_month_to_month_range_no_spaces_around_dash(self):
        """Test month to month range with no spaces around dash."""
        # Jan 1-Dec 7, 2020
        date_str = "Jan 1-Dec 7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Dec 7, 2020"
    
    def test_month_to_month_range_no_comma(self):
        """Test month to month range without comma."""
        # Jan 1-Dec 7 2020
        date_str = "Jan 1-Dec 7 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Dec 7, 2020"
    
    def test_month_to_month_range_with_spaces_around_dash(self):
        """Test month to month range with spaces around dash."""
        # Jan 1 - Dec 7, 2020
        date_str = "Jan 1 - Dec 7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Dec 7, 2020"
    
    def test_month_to_month_range_with_multiple_spaces_around_dash(self):
        """Test month to month range with multiple spaces around dash."""
        # Jan 1  -  Dec 7, 2020
        date_str = "Jan 1  -  Dec 7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Dec 7, 2020"
    
    def test_month_to_month_range_no_comma_with_spaces(self):
        """Test month to month range without comma but with spaces around dash."""
        # Jan 1 - Dec 7 2020
        date_str = "Jan 1 - Dec 7 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date == "Dec 7, 2020"
    
    def test_single_date(self):
        """Test single date (no range)."""
        date_str = "2020-01-01"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01"
        assert end_date is None
    
    def test_single_date_with_time(self):
        """Test single date with time."""
        date_str = "2020-01-01T14:30:45"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01T14:30:45"
        assert end_date is None
    
    def test_single_mdy_date(self):
        """Test single MDY date."""
        date_str = "01/01/2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "01/01/2020"
        assert end_date is None
    
    def test_single_month_date(self):
        """Test single month date."""
        date_str = "Jan 1, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Jan 1, 2020"
        assert end_date is None


# class TestSplitDateRangeStrWithCleanup:
#     """Test cases for split_date_range_str function with cleanup_date_str applied first."""
    
#     def test_iso_datetime_with_unicode_dash(self):
#         """Test ISO datetime format with unicode dash that needs cleanup."""
#         # Using unicode en dash (–) instead of regular dash
#         date_str = "2020-01-01T14:30:45 – 2020-01-07T14:30:45"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "2020-01-01T14:30:45"
#         assert end_date == "2020-01-07T14:30:45"
    
#     def test_iso_datetime_with_unicode_em_dash(self):
#         """Test ISO datetime format with unicode em dash (—) that needs cleanup."""
#         # Using unicode em dash (—) instead of regular dash
#         date_str = "2020-01-01T14:30:45 — 2020-01-07T14:30:45"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "2020-01-01T14:30:45"
#         assert end_date == "2020-01-07T14:30:45"
    
#     def test_iso_date_with_unicode_dash(self):
#         """Test ISO date format with unicode dash that needs cleanup."""
#         # Using unicode en dash (–) instead of regular dash
#         date_str = "2020-01-01 – 2020-01-07"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "2020-01-01"
#         assert end_date == "2020-01-07"
    
#     def test_mdy_date_with_unicode_dash(self):
#         """Test MDY date format with unicode dash that needs cleanup."""
#         # Using unicode en dash (–) instead of regular dash
#         date_str = "11/3/2021 – 11/10/2021"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "11/3/2021"
#         assert end_date == "11/10/2021"
    
#     def test_month_day_range_with_unicode_dash(self):
#         """Test month day range with unicode dash that needs cleanup."""
#         # Using unicode en dash (–) instead of regular dash
#         date_str = "Jan 1 – 7, 2020"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "Jan 1, 2020"
#         assert end_date == "Jan 7, 2020"
    
#     def test_month_to_month_range_with_unicode_dash(self):
#         """Test month to month range with unicode dash that needs cleanup."""
#         # Using unicode en dash (–) instead of regular dash
#         date_str = "Jan 1 – Dec 7, 2020"
#         cleaned_str = cleanup_date_str(date_str)
#         start_date, end_date = split_date_range_str(cleaned_str)
#         assert start_date == "Jan 1, 2020"
#         assert end_date == "Dec 7, 2020"


class TestSplitDateRangeStrEdgeCases:
    """Test edge cases and error conditions for split_date_range_str function."""
    
    def test_empty_string(self):
        """Test empty string."""
        date_str = ""
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == ""
        assert end_date is None
    
    def test_whitespace_only(self):
        """Test whitespace only string."""
        date_str = "   "
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == ""
        assert end_date is None
    
    def test_invalid_format_returns_single_date(self):
        """Test that invalid format returns the original string as start_date."""
        date_str = "invalid-date-format"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "invalid-date-format"
        assert end_date is None
    
    def test_partial_range_returns_single_date(self):
        """Test that partial range returns the original string as start_date."""
        date_str = "2020-01-01 -"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01 -"
        assert end_date is None
    
    def test_range_with_extra_text_returns_single_date(self):
        """Test that range with extra text returns the original string as start_date."""
        date_str = "2020-01-01 - 2020-01-07 extra text"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "2020-01-01"
        assert end_date == "2020-01-07"

class TestSplitDateRangeStrNonRomanCharacters:
    """Test cases for split_date_range_str function with non-Roman characters."""

    def test_cyrillic_month_range(self):
        """Test date range with months written in Cyrillic."""
        # Example: "Янв 1 - Янв 7, 2020" (Jan 1 - Jan 7, 2020 in Russian)
        date_str = "Янв 1 - Янв 7, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Янв 1, 2020"
        assert end_date == "Янв 7, 2020"

    def test_cyrillic_month_range_short(self):
        """Test day range with month in Cyrillic."""
        # Example: "Сент 1-15, 2020" (Sept 1-15, 2020 in Russian)
        date_str = "Сент 1-15, 2020"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Сент 1, 2020"
        assert end_date == "Сент 15, 2020"

    def test_cyrillic_month_single(self):
        """Test single date with month in Cyrillic."""
        date_str = "Март 15, 2021"
        start_date, end_date = split_date_range_str(date_str)
        assert start_date == "Март 15, 2021"
        assert end_date is None
