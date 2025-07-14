#!/usr/bin/env python3
"""
Test to verify that the granularity cleanup works correctly.
"""

from gtrend_api_tools.granularity import GranularityManager
from gtrend_api_tools.utils import load_config

def test_granularity_cleanup():
    """Test that calculate_search_granularity no longer accepts granularity parameter."""
    
    print("Testing granularity cleanup...")
    
    # Load config and create granularity manager
    config = load_config()
    gm = GranularityManager(config, verbose=False)
    
    # Test 1: Should work without granularity parameter
    print("\nTest 1: Should work without granularity parameter")
    result = gm.calculate_search_granularity(
        start_date="2023-01-01",
        end_date="2023-01-04"
    )
    print(f"✓ Successfully calculated granularity: {result['granularity']}")
    print(f"  Max units: {result['max_units']}")
    
    # Test 2: Should reject granularity parameter
    print("\nTest 2: Should reject granularity parameter")
    try:
        result = gm.calculate_search_granularity(
            start_date="2023-01-01",
            end_date="2023-01-04",
            granularity="D"  # This should fail
        )
        print("✗ ERROR: Function accepted granularity parameter when it shouldn't")
    except TypeError:
        print("✓ Function correctly rejected granularity parameter")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 3: Should not return blocks parameter
    print("\nTest 3: Should not return blocks parameter")
    result = gm.calculate_search_granularity(
        start_date="2023-01-01",
        end_date="2023-12-31"  # Long range
    )
    assert 'blocks' not in result, f"Expected no 'blocks' key, but found {result.get('blocks')}"
    print(f"✓ Correctly does not return blocks parameter")
    
    print("\n" + "=" * 50)
    print("All tests passed!")

if __name__ == "__main__":
    test_granularity_cleanup() 