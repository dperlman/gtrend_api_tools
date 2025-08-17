import pytest
from datetime import datetime, timezone
from gtrend_api_tools.search_specs import SearchSpec

# Configure which API to test - change this to test different APIs
API_TO_TEST = 'applescript_safari'
BATCH_METHOD = "sequential"  # options are 'thread' or 'sequential'
MAX_WORKERS = 10
NUMBER_OF_SPECS = 10

@pytest.mark.parametrize('api_instance', [API_TO_TEST], indirect=True)
def test_execute_batch(api_instance, test_terms, test_dates):
    """
    Test the batch execution using the search_batch method.
    
    Creates a batch of three searches with different terms and date ranges,
    executes them using the specified method, and verifies the results.
    """
    print(f"\n🧪 Testing {API_TO_TEST} batch execution with {BATCH_METHOD} method and {MAX_WORKERS} workers")
    
    # Create a main search specification as a template
    main_spec = SearchSpec(
        search_term=test_terms['term5'],
        start=test_dates['short_range']['start'],
        end=test_dates['short_range']['end'],
        api=API_TO_TEST
    )
    
    # Create a list of search specifications for the batch
    spec_list = [
        # First spec: different term, same date range
        SearchSpec(
            search_term=test_terms['term1'],
            start=test_dates['short_range']['start'],
            end=test_dates['short_range']['end'],
            api=API_TO_TEST
        ),
        # Second spec: same term, different date range
        SearchSpec(
            search_term=test_terms['term2'],
            start=test_dates['medium_range']['start'],
            end=test_dates['medium_range']['end'],
            api=API_TO_TEST
        ),
        # Third spec: different term, different date range
        SearchSpec(
            search_term=test_terms['term3'],
            start=test_dates['long_range']['start'],
            end=test_dates['long_range']['end'],
            api=API_TO_TEST
        )
    ]
    
    print(f"📋 Created {len(spec_list)} search specifications:")
    for i, spec in enumerate(spec_list):
        print(f"   {i+1}. Term: '{spec.term_string}', Date range: {spec.str.search_range_ymd}")
    
    # Execute the batch using the API's search_batch method
    print(f"\n🚀 Executing batch search with {BATCH_METHOD} method...")
    results = api_instance.search_batch(
        search_spec_list=spec_list,
        method=BATCH_METHOD,
        max_workers=MAX_WORKERS
    )
    print(f"✅ Batch search executed successfully with method '{BATCH_METHOD}' and {MAX_WORKERS} workers")
    
    print(f"\n📊 Analyzing results...")
    
    # Check that we got exactly 3 results (one for each search)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print(f"✅ Found {len(results)} results as expected")
    
    # Check that there were no errors
    error_count = sum(1 for r in results if getattr(r, 'is_error', False))
    assert error_count == 0, f"Expected 0 errors, got {error_count}"
    print(f"✅ No errors occurred ({error_count} errors found)")
    
    # Calculate progress
    completed = sum(1 for r in results if not getattr(r, 'is_error', False))
    total = len(spec_list)
    percentage = (completed / total) * 100.0 if total > 0 else 0.0
    
    # Check progress
    assert completed == 3, f"Expected 3 completed, got {completed}"
    assert total == 3, f"Expected 3 total, got {total}"
    assert percentage == 100.0, f"Expected 100% completion, got {percentage}%"
    print(f"✅ Batch completed successfully: {completed}/{total} ({percentage:.1f}%)")
    
    # Verify each result has the expected structure
    print(f"\n🔍 Verifying individual results...")
    for i, result in enumerate(results):
        print(f"\n   Result {i+1} (Term: '{result.search_spec.term_string}'):")
        term_list = [i.strip().replace(' ', '_').lower() for i in result.search_spec.term_string.split(',')]
        
        
        # Check that each result is a TrendSearchResult
        assert hasattr(result, 'raw_data'), f"Result {i} missing raw_data"
        assert hasattr(result, 'data'), f"Result {i} missing data"
        assert hasattr(result, 'dataframe'), f"Result {i} missing dataframe"
        assert hasattr(result, 'search_spec'), f"Result {i} missing search_spec"
        print(f"     ✅ Has all required attributes")

        # Check that the search_spec matches what we expect
        expected_spec = spec_list[i]
        assert result.search_spec.term_string == expected_spec.term_string, \
            f"Result {i} term mismatch: expected {expected_spec.term_string}, got {result.search_spec.term_string}"
        print(f"     ✅ Search spec matches: {expected_spec.term_string}")
        
        # Check that we have data
        assert result.data is not None, f"Result {i} has no data"
        assert len(result.data) > 0, f"Result {i} has empty data"
        assert len(result.data) > 6, f"Result {i} has too little data: {len(result.data)}"
        print(f"     ✅ Has {len(result.data)} data points")
        
        # Check that we can get a DataFrame
        df = result.dataframe
        assert not df.empty, f"Result {i} has empty DataFrame"
        
        # Check that the DataFrame has the expected column (sanitized term)
        for term in term_list:
            assert term in df.columns, \
                f"Result {i} DataFrame missing expected column '{term}'. Available columns: {list(df.columns)}"
            print(f"     ✅ DataFrame has expected column: {term}")
        assert term_list == list(df.columns), f"Result {i} DataFrame columns do not match expected order ofcolumns: {term_list} != {list(df.columns)}"
        print(f"     ✅ DataFrame shape: {df.shape}")
    
    # Verify the results are different (different terms and/or date ranges)
    print(f"\n🔍 Verifying result diversity...")
    assert results[0].search_spec.term_string != results[1].search_spec.term_string, \
        "First two results should have different terms"
    assert results[0].search_spec.start_dt != results[1].search_spec.start_dt or \
           results[0].search_spec.end_dt != results[1].search_spec.end_dt, \
        "First two results should have different date ranges"
    print(f"✅ Results have different terms and date ranges as expected")
    
    print(f"\n🎉 Batch test completed successfully!")
    print(f"   📈 Summary: {completed} results, {error_count} errors")
    print(f"   📊 Progress: {completed}/{total} ({percentage:.1f}%)")
    print(f"   🔧 Method: {BATCH_METHOD} with {MAX_WORKERS} workers")
    print(f"   🎯 API: {API_TO_TEST}")




@pytest.mark.parametrize('spec_list', [(NUMBER_OF_SPECS, API_TO_TEST)], indirect=True)
@pytest.mark.parametrize('api_instance', [API_TO_TEST], indirect=True)
def test_variable_batch_size(api_instance, spec_list):
    """
    Test batch execution with variable batch sizes using the spec_list fixture.
    
    This test uses the spec_list fixture to automatically generate SearchSpec objects
    based on the NUMBER_OF_SPECS and API_TO_TEST constants.
    """
    print(f"\n🧪 Testing variable batch size with {API_TO_TEST}")
    print(f"   📊 Batch size: {len(spec_list)}")
    print(f"   🔧 Method: {BATCH_METHOD} with {MAX_WORKERS} workers")
    
    # Display the specs that were created
    print(f"\n📋 Using {len(spec_list)} search specifications:")
    # for i, spec in enumerate(spec_list):
    #     print(f"   {i+1}. Term: '{spec.term_string}', Date range: {spec.str.search_range_ymd}")
    
    # Execute the batch using the API's search_batch method
    print(f"\n🚀 Executing batch search with {BATCH_METHOD} method...")
    results = api_instance.search_batch(
        search_spec_list=spec_list,
        method=BATCH_METHOD,
        max_workers=MAX_WORKERS
    )
    print(f"✅ Batch search executed successfully with method '{BATCH_METHOD}' and {MAX_WORKERS} workers")
    
    for result in results:
        print(result.search_spec.term_string)
        print(result.data[:1000])

    print(f"\n📊 Analyzing results...")
    
    # Check that we got the expected number of results
    expected_count = len(spec_list)
    assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"
    print(f"✅ Found {len(results)} results as expected")
    
    # Check that there were no errors
    error_count = sum(1 for r in results if getattr(r, 'is_error', False))
    assert error_count == 0, f"Expected 0 errors, got {error_count}"
    print(f"✅ No errors occurred ({error_count} errors found)")
    
    # Calculate progress
    completed = sum(1 for r in results if not getattr(r, 'is_error', False))
    total = len(spec_list)
    percentage = (completed / total) * 100.0 if total > 0 else 0.0
    
    # Check progress
    assert completed == expected_count, f"Expected {expected_count} completed, got {completed}"
    assert total == expected_count, f"Expected {expected_count} total, got {total}"
    assert percentage == 100.0, f"Expected 100% completion, got {percentage}%"
    print(f"✅ Batch completed successfully: {completed}/{total} ({percentage:.1f}%)")
    
    # Verify each result has the expected structure
    print(f"\n🔍 Verifying individual results...")
    
    # Track HTTP response codes
    http_codes = {}
    
    for i, result in enumerate(results):
        print(f"\n   Result {i+1} (Term: '{result.search_spec.term_string}'):")
        
        # Count HTTP response codes
        if hasattr(result, 'response') and result.response is not None:
            status_code = result.response.status_code
            http_codes[status_code] = http_codes.get(status_code, 0) + 1
            print(f"     📡 HTTP Status: {status_code}")
        else:
            print(f"     📡 HTTP Status: No response object")
    
    # Report HTTP response code summary
    print(f"\n📊 HTTP Response Code Summary:")
    if http_codes:
        for status_code, count in sorted(http_codes.items()):
            print(f"   {status_code}: {count} requests")
    else:
        print(f"   No HTTP response codes recorded")
    

    for i, result in enumerate(results):
        # Check that each result is a TrendSearchResult
        assert hasattr(result, 'raw_data'), f"Result {i} missing raw_data"
        assert hasattr(result, 'data'), f"Result {i} missing data"
        assert hasattr(result, 'dataframe'), f"Result {i} missing dataframe"
        assert hasattr(result, 'search_spec'), f"Result {i} missing search_spec"
        print(f"     ✅ Has all required attributes")

        # Check that the search_spec matches what we expect
        expected_spec = spec_list[i]
        assert result.search_spec.term_string == expected_spec.term_string, \
            f"Result {i} term mismatch: expected {expected_spec.term_string}, got {result.search_spec.term_string}"
        print(f"     ✅ Search spec matches: {expected_spec.term_string}")
        
        # Check that we have data
        assert result.data is not None, f"Result {i} has no data"
        assert len(result.data) > 0, f"Result {i} has empty data"
        assert len(result.data) > 6, f"Result {i} has too little data: {len(result.data)}"
        print(f"     ✅ Has {len(result.data)} data points")
        
        # Check that we can get a DataFrame
        df = result.dataframe
        assert not df.empty, f"Result {i} has empty DataFrame"
        
        # Check that the DataFrame has the expected column (sanitized term)
        term_list = [i.strip().replace(' ', '_').lower() for i in result.search_spec.term_string.split(',')]
        for term in term_list:
            assert term in df.columns, \
                f"Result {i} DataFrame missing expected column '{term}'. Available columns: {list(df.columns)}"
            print(f"     ✅ DataFrame has expected column: {term}")
        assert term_list == list(df.columns), f"Result {i} DataFrame columns do not match expected order ofcolumns: {term_list} != {list(df.columns)}"
        print(f"     ✅ DataFrame shape: {df.shape}")
    

    print(f"\n🎉 Variable batch size test completed successfully!")
    print(f"   📈 Summary: {completed} results, {error_count} errors")
    print(f"   📊 Progress: {completed}/{total} ({percentage:.1f}%)")
    print(f"   🔧 Method: {BATCH_METHOD} with {MAX_WORKERS} workers")
    print(f"   🎯 API: {API_TO_TEST}")
    print(f"   📦 Batch size: {NUMBER_OF_SPECS}") 

