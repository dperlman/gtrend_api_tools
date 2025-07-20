import pytest
from datetime import datetime, timezone
from gtrend_api_tools.APIs.batch import TrendSearchBatch
from gtrend_api_tools.search_specs import SearchSpec

# Configure which API to test - change this to test different APIs
API_TO_TEST = 'searchapi'

@pytest.mark.parametrize('api_key,api_instance', [(API_TO_TEST, API_TO_TEST)], indirect=True)
def test_execute_iterate(api_instance, test_terms, test_dates):
    """
    Test the batch execution using the iterate method.
    
    Creates a batch of three searches with different terms and date ranges,
    executes them sequentially, and verifies the results.
    """
    # Create a main search specification as a template
    main_spec = SearchSpec(
        search_term=test_terms['term1'],
        start=test_dates['short_range']['start'],
        end=test_dates['short_range']['end'],
        api=API_TO_TEST
    )
    
    # Create a list of search specifications for the batch
    spec_list = [
        # First spec: different term, same date range
        SearchSpec(
            search_term=test_terms['term2'],
            start=test_dates['short_range']['start'],
            end=test_dates['short_range']['end'],
            api=API_TO_TEST
        ),
        # Second spec: same term, different date range
        SearchSpec(
            search_term=test_terms['term1'],
            start=test_dates['medium_range']['start'],
            end=test_dates['medium_range']['end'],
            api=API_TO_TEST
        ),
        # Third spec: different term, different date range
        SearchSpec(
            search_term=test_terms['term3'],
            start=test_dates['medium_range']['start'],
            end=test_dates['medium_range']['end'],
            api=API_TO_TEST
        )
    ]
    
    # Create the batch processor
    batch = TrendSearchBatch(
        main_spec=main_spec,
        spec_list=spec_list,
        method="iterate"
    )
    
    # Execute the batch
    batch.execute(api_instance)
    
    # Verify the results
    results = batch.get_results()
    errors = batch.get_errors()
    progress = batch.get_progress()
    
    # Check that we got exactly 3 results (one for each search)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    
    # Check that there were no errors
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}: {errors}"
    
    # Check progress
    assert progress['completed'] == 3, f"Expected 3 completed, got {progress['completed']}"
    assert progress['total'] == 3, f"Expected 3 total, got {progress['total']}"
    assert progress['percentage'] == 100.0, f"Expected 100% completion, got {progress['percentage']}%"
    
    # Verify each result has the expected structure
    for i, result in enumerate(results):
        # Check that each result is a TrendSearchResult
        assert hasattr(result, 'raw_data'), f"Result {i} missing raw_data"
        assert hasattr(result, 'data'), f"Result {i} missing data"
        assert hasattr(result, 'dataframe'), f"Result {i} missing dataframe"
        assert hasattr(result, 'search_spec'), f"Result {i} missing search_spec"
        
        # Check that the search_spec matches what we expect
        expected_spec = spec_list[i]
        assert result.search_spec.term_string == expected_spec.term_string, \
            f"Result {i} term mismatch: expected {expected_spec.term_string}, got {result.search_spec.term_string}"
        
        # Check that we have data
        assert result.data is not None, f"Result {i} has no data"
        assert len(result.data) > 0, f"Result {i} has empty data"
        
        # Check that we can get a DataFrame
        df = result.dataframe
        assert not df.empty, f"Result {i} has empty DataFrame"
        
        # Check that the DataFrame has the expected column (sanitized term)
        expected_column = expected_spec.term_string.replace(' ', '_').lower()
        assert expected_column in df.columns, \
            f"Result {i} DataFrame missing expected column '{expected_column}'. Available columns: {list(df.columns)}"
    
    # Verify the results are different (different terms and/or date ranges)
    assert results[0].search_spec.term_string != results[1].search_spec.term_string, \
        "First two results should have different terms"
    assert results[0].search_spec.start_dt != results[1].search_spec.start_dt or \
           results[0].search_spec.end_dt != results[1].search_spec.end_dt, \
        "First two results should have different date ranges"
    
    print(f"✅ Batch test completed successfully with {len(results)} results and {len(errors)} errors")
    print(f"   Progress: {progress['completed']}/{progress['total']} ({progress['percentage']:.1f}%)") 