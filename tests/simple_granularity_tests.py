"""
Simple granularity tests without pytest - importing test data from search_fixtures.
"""
from datetime import datetime, timezone 
from gtrend_api_tools.granularity import GranularityManager

granularity_manager = GranularityManager(api='brightdata')
# Import the fixture functions and call them to get the data
from fixtures.search_fixtures import granularity_test_dict

GRANULARITY_TEST_DATES = granularity_test_dict

print(granularity_manager.rules)

# Example usage:
if __name__ == "__main__":
    print("Testing GranularityManager with fixture data:")
    print("=" * 60)
    
    for test_name, test_data in GRANULARITY_TEST_DATES.items():
        start_date = test_data['start']
        end_date = test_data['end']
        expected_granularity = test_data['granularity']
        expected_rows = test_data['expected_rows']
        
        # Calculate granularity using the manager
        result = granularity_manager.calculate_search_granularity(start_date, end_date)
        calculated_granularity = result['granularity']
        
        # Check if they match
        status = "✓ PASS" if calculated_granularity == expected_granularity else "✗ FAIL"
        
        print(f"{test_name:20} | Expected: {expected_granularity} | Calculated: {calculated_granularity} | {status}")
        print(f"{'':20} | Date range: {start_date} to {end_date}")
        print(f"{'':20} | Expected rows: {expected_rows}")
        print()
    
    print("=" * 60)
    print("Test completed!")
