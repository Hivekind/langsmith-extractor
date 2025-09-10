# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-04-zenrows-error-categorization/spec.md

> Created: 2025-09-04
> Status: Ready for Implementation

## Tasks

### 1. Error Category Management System

Create the foundational error categorization system based on comprehensive production data analysis.

1.1. **Write tests for error category management**
- Create `tests/test_error_categories.py` with test cases for ErrorCategoryManager class
- Test loading of 6 main error categories with correct patterns and metadata
- Test dynamic category addition and unknown error fallback logic
- Test category pattern matching against real production error messages

1.2. **Implement ErrorCategoryManager class**
- Create `lse/error_categories.py` module with ErrorCategoryManager class
- Define ERROR_CATEGORIES dictionary with 6 categories from production analysis:
  - http_404_not_found (50.4% frequency)
  - http_422_unprocessable (18.2% frequency) 
  - http_413_too_large (12.4% frequency)
  - read_timeout (13.2% frequency)
  - http_400_bad_request (5.8% frequency)
  - http_503_service_unavailable (0.8% frequency)
- Implement pattern matching logic with compiled regex for performance

1.3. **Implement error categorization function**
- Create `categorize_zenrows_error(error_record: Dict) -> str` function in `lse/analysis.py`
- Implement classification logic using ErrorCategoryManager
- Add unknown_errors fallback for unclassified patterns
- Handle edge cases with incomplete or ambiguous error messages

1.4. **Add unknown error logging system**
- Implement logging for unclassified errors to `logs/unknown_errors.log`
- Include timestamp, project, trace_id, and full error message
- Add `--debug-unknown-errors` CLI flag for development analysis
- Create log rotation and size management

1.5. **Validate categorization against production data**
- Test categorization function against comprehensive production error dataset
- Verify 100% classification accuracy for the 6 main error categories
- Validate frequency percentages match production analysis
- Test error message variations and edge cases

1.6. **Performance optimization for categorization**
- Compile regex patterns once during initialization
- Implement caching for repeated error patterns
- Optimize string matching algorithms for large datasets
- Add performance benchmarks for 10,000+ trace processing

1.7. **Integration testing with existing codebase**
- Test ErrorCategoryManager integration with existing analysis.py functions
- Verify no breaking changes to existing error extraction logic
- Test memory usage and performance impact on existing workflows
- Validate thread safety for concurrent processing

1.8. **Verify all error category management tests pass**
- Run complete test suite for error categorization system
- Verify test coverage meets minimum 95% for new error category code
- Validate performance benchmarks meet scalability targets
- Check integration tests pass with existing codebase

### 2. Data Structure and Analysis Updates

Update the data processing pipeline to collect and aggregate error category statistics.

2.1. **Write tests for updated data structures**
- Create test cases in `tests/test_analysis.py` for category-enhanced data structures
- Test error record modification to include category field
- Test category aggregation across multiple dates and projects
- Test backward compatibility with existing data structure consumers

2.2. **Modify error extraction to include categories**
- Update `extract_zenrows_errors()` function in `lse/analysis.py`
- Add category field to error record dictionaries
- Integrate categorize_zenrows_error() function calls
- Maintain existing error extraction logic and performance

2.3. **Update analyze_zenrows_errors method**
- Modify return data structure to include category breakdowns
- Implement category count aggregation in daily statistics
- Add validation logic to ensure category counts sum to total errors
- Maintain backward compatibility with existing consumers

2.4. **Implement category aggregation logic**
- Update `calculate_error_rates()` to handle category aggregation across date ranges
- Implement category summing for multi-project reports
- Add percentage calculations for category columns
- Handle edge cases with zero errors or missing categories

2.5. **Add data structure validation**
- Implement validation functions to ensure data integrity
- Verify category counts sum to total error count
- Add checks for missing or invalid category data
- Create validation tests for edge cases and error conditions

2.6. **Memory optimization for large datasets** 
- Implement streaming processing for large trace files
- Use generators where possible to minimize memory footprint
- Optimize nested loop processing in error extraction
- Add memory usage monitoring and limits

2.7. **Backward compatibility testing**
- Test existing data structure consumers work unchanged
- Verify existing aggregation logic continues to function
- Test multi-project and date-range aggregation accuracy
- Validate error detection logic remains consistent

2.8. **Verify all data structure update tests pass**
- Run complete test suite for updated analysis functions
- Verify category aggregation accuracy against known datasets
- Check performance benchmarks for large dataset processing
- Validate backward compatibility with existing workflows

### 3. CSV Output Format Enhancement

Enhance the CSV output format to include error category columns while maintaining backward compatibility.

3.1. **Write tests for enhanced CSV output**
- Create test cases in `tests/test_formatters.py` for new CSV format
- Test new category column generation and ordering
- Test backward compatibility with existing CSV consumers
- Test multi-date and multi-project CSV output formats

3.2. **Update ReportFormatter class**
- Modify `ReportFormatter.format_zenrows_report()` in `lse/formatters.py`
- Add new category columns to CSV header generation
- Update row data generation to include category counts
- Ensure proper column ordering and data types

3.3. **Implement dynamic column generation**
- Generate CSV headers dynamically based on active error categories
- Handle new categories without code changes to output format
- Maintain fixed column positions for existing columns
- Add support for category metadata in column headers

3.4. **Add CSV data validation**
- Implement validation that category counts sum to total errors
- Add checks for data consistency across columns
- Validate percentage calculations for category columns
- Create error handling for malformed category data

3.5. **Enhance aggregation for CSV output**
- Update aggregation logic for multi-date reports with categories
- Implement proper percentage calculations across date ranges
- Add summary statistics for category distributions
- Handle edge cases with varying categories across dates

3.6. **Performance optimization for CSV generation**
- Optimize CSV writing for large datasets
- Implement efficient column formatting and data conversion
- Add progress indicators for long-running CSV generation
- Minimize memory usage during CSV output creation

3.7. **Backward compatibility validation**
- Test that existing scripts consuming CSV output continue to work
- Verify no changes to existing column positions or data types
- Test CSV parsing with both old and new format consumers
- Validate data accuracy remains unchanged in existing columns

3.8. **Verify all CSV output enhancement tests pass**
- Run complete test suite for updated formatter functionality
- Verify CSV output format matches specification requirements
- Check performance benchmarks for large CSV generation
- Validate backward compatibility with existing CSV consumers

### 4. CLI Integration and Command Enhancement

Integrate the error categorization system with the existing CLI commands and enhance user experience.

4.1. **Write tests for CLI integration**
- Create test cases in `tests/test_cli.py` for enhanced zenrows-errors command
- Test command functionality with category outputs
- Test --debug-unknown-errors flag implementation
- Test command performance with large datasets

4.2. **Update zenrows-errors command**
- Modify CLI command to use enhanced categorization system
- Ensure no changes to existing command parameters or flags
- Add --debug-unknown-errors flag for development analysis
- Maintain existing command output and functionality

4.3. **Implement CLI feedback enhancements**
- Add progress indicators for category processing phases
- Implement verbose output options for debugging
- Add category statistics to command output summary
- Create helpful error messages for categorization issues

4.4. **Add CLI validation and error handling**
- Implement proper error handling for categorization failures
- Add validation for command parameters with category features
- Create meaningful error messages for edge cases
- Handle graceful degradation when categorization fails

4.5. **Performance monitoring and reporting**
- Add timing metrics for categorization processing phases
- Implement memory usage monitoring and reporting
- Create performance warnings for large datasets
- Add optional performance benchmarking output

4.6. **CLI documentation updates**
- Update command help text to reflect new category features
- Add examples of enhanced CSV output format
- Document --debug-unknown-errors flag usage
- Create usage examples for category analysis workflows

4.7. **Integration testing with existing CLI**
- Test CLI integration with existing archive and report commands
- Verify no breaking changes to existing CLI workflows
- Test CLI performance with various dataset sizes
- Validate CLI output formatting and user experience

4.8. **Verify all CLI integration tests pass**
- Run complete CLI test suite including enhanced commands
- Verify command functionality meets specification requirements
- Check performance benchmarks for CLI command execution
- Validate user experience and output formatting quality

### 5. Production Validation and Performance Testing

Validate the complete implementation against production data and ensure performance requirements are met.

5.1. **Write comprehensive integration tests**
- Create end-to-end test cases using production data samples
- Test complete workflow from trace processing to CSV output
- Test performance with 10,000+ traces per dataset
- Test memory usage and processing time benchmarks

5.2. **Production data validation testing**
- Test categorization accuracy against comprehensive production dataset
- Validate error distribution percentages match production analysis
- Test edge cases found in production data
- Verify all 6 main error categories are correctly classified

5.3. **Performance benchmarking**
- Implement performance tests for scalability targets
- Test processing 10,000+ traces per day without degradation
- Verify sub-second response for single-day reports
- Test multi-month date range processing under 5 minutes

5.4. **Memory usage optimization validation**
- Test memory usage with large datasets and trace files
- Verify memory footprint stays within acceptable limits
- Test streaming processing effectiveness for large files
- Validate memory leak prevention and garbage collection

5.5. **Backward compatibility validation**
- Test complete backward compatibility with existing scripts
- Verify existing automation and reporting continues to work
- Test CSV parsing by existing downstream systems
- Validate data accuracy and format consistency

5.6. **Error handling and edge case testing**
- Test system behavior with malformed trace data
- Validate graceful handling of network errors during processing
- Test unknown error logging and categorization fallbacks
- Verify system stability under various error conditions

5.7. **Documentation and validation reporting**
- Create validation report documenting test results and coverage
- Document performance benchmarks and scalability limits
- Create troubleshooting guide for common issues
- Document known limitations and edge cases

5.8. **Verify all production validation tests pass**
- Run complete test suite including integration and performance tests
- Verify all acceptance criteria from specification are met
- Check that implementation meets all technical requirements
- Validate production readiness and deployment requirements