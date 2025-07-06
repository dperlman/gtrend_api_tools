#!/usr/bin/env python3
"""
Quick test to verify GtrendDateRange changes work correctly.
"""

from gtrend_api_tools.search_specs import GtrendDateRange, DateRange

def test_changes():
    """Test that GtrendDateRange works correctly without granularity parameter."""
    
    print("Testing GtrendDateRange changes...")
    
    # Test 1: GtrendDateRange should work without granularity parameter
    print("\nTest 1: GtrendDateRange automatic granularity")
    dr1 = GtrendDateRange(
        start_date="2023-01-01",
        end_date="2023-01-04",
        verbose=False
    )
    print(f"✓ GtrendDateRange created successfully: {dr1}")
    print(f"  Granularity: {dr1.granularity}")
    print(f"  Max units: {dr1.get_max_units()}")
    
    # Test 2: GtrendDateRange should not accept granularity parameter
    print("\nTest 2: GtrendDateRange should reject granularity parameter")
    try:
        dr2 = GtrendDateRange(
            start_date="2023-01-01",
            end_date="2023-01-04",
            granularity="W",  # This should fail
            verbose=False
        )
        print("✗ ERROR: GtrendDateRange accepted granularity parameter when it shouldn't")
    except TypeError:
        print("✓ GtrendDateRange correctly rejected granularity parameter")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 3: DateRange should still accept granularity parameter
    print("\nTest 3: DateRange should still accept granularity parameter")
    dr3 = DateRange(
        start_date="2023-01-01",
        end_date="2023-01-04",
        granularity="W",
        verbose=False
    )
    print(f"✓ DateRange created successfully with explicit granularity: {dr3}")
    print(f"  Granularity: {dr3.granularity}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    test_changes() 