# Phase 16: Availability Dataset Curation (Best 100)

## Overview
Implement intelligent dataset curation for availability evaluation datasets with the `--best-100` CLI parameter. This feature creates optimally balanced 100-example datasets with comprehensive negative case coverage and representative positive examples for high-quality availability testing.

**⚠️ Critical Constraint**: The `--best-100` parameter is **EXCLUSIVELY for `--eval-type availability`**. It is NOT supported for `token_name` or `website` eval types and will show a clear error message if attempted with other eval types.

## Problem Statement

### Current Limitation
The existing `lse eval create-dataset --eval-type availability` command creates datasets containing ALL examples from a given date range, which can result in:

1. **Unwieldy Dataset Sizes**: 60+ examples per day create datasets too large for efficient evaluation
2. **Limited Negative Coverage**: False availability cases may be sparse across large datasets
3. **Redundant Positive Cases**: Many similar positive examples without strategic selection
4. **Domain Concentration**: Lack of diversity in website types and domains tested

### Business Need
Users need **curated, high-quality datasets** that:
- **Maximize Test Coverage**: Include all critical negative cases for comprehensive testing
- **Optimize for Evaluation**: Manageable size (~100 examples) for efficient evaluation workflows  
- **Ensure Representativeness**: Diverse positive examples covering various website types and domains
- **Maintain Quality**: No duplicate URLs, complete data, and balanced distributions

## Solution Architecture

### Core Principle: Intelligent Curation
The `--best-100` feature implements a multi-stage curation algorithm:

1. **Negative Case Priority**: Include ALL `is_available: false` examples (deduplicated by URL)
2. **Positive Case Optimization**: Select representative `is_available: true` examples with domain diversity
3. **Quality Assurance**: Validate dataset meets size, uniqueness, and completeness requirements
4. **Statistical Reporting**: Provide clear metrics on curation results

### Technical Design

#### CLI Integration
```bash
# ✅ VALID: New curated mode (availability only)
lse eval create-dataset --project my-project --eval-type availability --date 2025-09-10 --best-100 --output curated.jsonl --name curated_availability

# ✅ VALID: Existing behavior unchanged (without --best-100)  
lse eval create-dataset --project my-project --eval-type availability --date 2025-09-10 --output all.jsonl --name all_availability

# ❌ INVALID: --best-100 with non-availability eval types (will error)
lse eval create-dataset --project my-project --eval-type token_name --date 2025-09-10 --best-100 --output error.jsonl --name error
lse eval create-dataset --project my-project --eval-type website --date 2025-09-10 --best-100 --output error.jsonl --name error
```

#### Curation Algorithm Design

**Stage 1: Negative Case Collection**
```python
def _extract_negative_examples(self, all_examples: List[DatasetExample]) -> List[DatasetExample]:
    """Extract and deduplicate all negative availability examples."""
    negative_examples = [ex for ex in all_examples if not ex.outputs.get('is_available', True)]
    
    # Deduplicate by website_url, keeping most recent
    unique_negatives = {}
    for example in sorted(negative_examples, key=lambda x: x.metadata.get('created_at', ''), reverse=True):
        url = example.inputs.get('website_url')
        if url not in unique_negatives:
            unique_negatives[url] = example
    
    return list(unique_negatives.values())
```

**Stage 2: Positive Case Selection**
```python
def _select_representative_positive_examples(
    self, all_examples: List[DatasetExample], target_count: int
) -> List[DatasetExample]:
    """Select diverse, high-quality positive examples."""
    positive_examples = [ex for ex in all_examples if ex.outputs.get('is_available', False)]
    
    # Group by domain for diversity
    domain_groups = defaultdict(list)
    for example in positive_examples:
        domain = self._extract_domain(example.inputs.get('website_url', ''))
        domain_groups[domain].append(example)
    
    # Select best example from each domain
    selected = []
    for domain, examples in domain_groups.items():
        best_example = max(examples, key=self._calculate_quality_score)
        selected.append(best_example)
        if len(selected) >= target_count:
            break
    
    # Fill remaining slots with highest quality examples
    if len(selected) < target_count:
        remaining = [ex for ex in positive_examples if ex not in selected]
        additional = sorted(remaining, key=self._calculate_quality_score, reverse=True)
        selected.extend(additional[:target_count - len(selected)])
    
    return selected[:target_count]
```

**Stage 3: Quality Scoring System**
```python
def _calculate_quality_score(self, example: DatasetExample) -> float:
    """Calculate quality score for positive examples."""
    score = 0.0
    
    # Base score for availability
    if example.outputs.get('is_available', False):
        score += 1.0
    
    # Bonus for detailed notes
    notes = example.outputs.get('notes', '')
    if notes and len(notes) > 20:
        score += 0.5
    
    # Bonus for successful scraping indicators
    if 'successfully scraped' in notes.lower():
        score += 0.3
    elif 'analysis completed' in notes.lower():
        score += 0.2
    
    # Penalty for generic/unclear notes
    if 'status unclear' in notes.lower():
        score -= 0.2
    
    return score
```

## Implementation Plan

### Phase 16.1: CLI and Framework Integration

#### CLI Parameter Addition
```python
# In lse/commands/eval.py
@click.option(
    '--best-100',
    is_flag=True,
    help='Create curated dataset with ~100 representative examples (ONLY for --eval-type availability)'
)
def create_dataset(
    project: str,
    eval_type: str,
    date: str,
    output: str,
    name: str,
    best_100: bool = False
):
    """Create evaluation dataset from database."""
    # ⚠️ CRITICAL: --best-100 ONLY works with availability eval_type
    if best_100 and eval_type != "availability":
        console.print("[red]Error: --best-100 is only supported for --eval-type availability[/red]")
        console.print("[yellow]Tip: Use --eval-type availability with --best-100, or remove --best-100 for other eval types[/yellow]")
        raise typer.Exit(1)
    
    # Pass curation flag to dataset builder
    dataset_builder = DatasetBuilder(curation_enabled=best_100)
    # ... rest of implementation
```

#### DatasetBuilder Enhancement
```python
# In lse/evaluation.py
class DatasetBuilder:
    def __init__(self, storage=None, database=None, curation_enabled: bool = False):
        self.storage = storage
        self.database = database
        self.curation_enabled = curation_enabled
    
    async def create_dataset_from_db(
        self, 
        project: str, 
        start_date: str, 
        end_date: str, 
        eval_type: str
    ) -> EvaluationDataset:
        """Create dataset with optional curation."""
        # Extract all examples (existing logic)
        all_examples = await self._extract_all_examples(project, start_date, end_date, eval_type)
        
        # Apply curation if enabled for availability
        if self.curation_enabled and eval_type == "availability":
            curated_examples = self._curate_dataset(all_examples, target_size=100)
            self._print_curation_statistics(all_examples, curated_examples)
            return EvaluationDataset(examples=curated_examples)
        
        # Return all examples (existing behavior)
        return EvaluationDataset(examples=all_examples)
```

### Phase 16.2: Curation Logic Implementation

#### Core Curation Method
```python
def _curate_dataset(
    self, all_examples: List[DatasetExample], target_size: int = 100
) -> List[DatasetExample]:
    """Apply intelligent curation to create optimal dataset."""
    
    # Stage 1: Collect all negative examples
    negative_examples = self._extract_negative_examples(all_examples)
    console.print(f"[blue]Found {len(negative_examples)} unique negative examples (is_available: false)[/blue]")
    
    # Stage 2: Select representative positive examples
    remaining_slots = target_size - len(negative_examples)
    positive_examples = self._select_representative_positive_examples(
        all_examples, target_count=remaining_slots
    )
    console.print(f"[blue]Selected {len(positive_examples)} representative positive examples[/blue]")
    
    # Stage 3: Combine and validate
    curated_examples = negative_examples + positive_examples
    self._validate_curated_dataset(curated_examples)
    
    return curated_examples[:target_size]  # Final size limit
```

#### Domain Diversity Optimization
```python
def _extract_domain(self, url: str) -> str:
    """Extract domain from URL for diversity analysis."""
    try:
        parsed = urllib.parse.urlparse(url if url.startswith('http') else f'http://{url}')
        domain = parsed.netloc.lower()
        # Remove www. prefix for grouping
        return domain.replace('www.', '')
    except:
        return 'unknown'

def _analyze_domain_diversity(self, examples: List[DatasetExample]) -> Dict[str, int]:
    """Analyze domain distribution in curated dataset."""
    domain_counts = defaultdict(int)
    for example in examples:
        domain = self._extract_domain(example.inputs.get('website_url', ''))
        domain_counts[domain] += 1
    return dict(domain_counts)
```

### Phase 16.3: Quality Validation and Reporting

#### Dataset Validation
```python
def _validate_curated_dataset(self, examples: List[DatasetExample]) -> None:
    """Validate curated dataset meets quality requirements."""
    
    # Check URL uniqueness
    urls = [ex.inputs.get('website_url') for ex in examples]
    if len(urls) != len(set(urls)):
        raise ValueError("Curated dataset contains duplicate website_urls")
    
    # Check data completeness
    for i, example in enumerate(examples):
        if not example.inputs.get('website_url'):
            raise ValueError(f"Example {i} missing website_url")
        if 'is_available' not in example.outputs:
            raise ValueError(f"Example {i} missing is_available field")
    
    console.print(f"[green]✓ Dataset validation passed: {len(examples)} examples[/green]")
```

#### Statistical Reporting
```python
def _print_curation_statistics(
    self, original_examples: List[DatasetExample], curated_examples: List[DatasetExample]
) -> None:
    """Print detailed curation statistics."""
    
    # Count negative/positive split
    negative_count = sum(1 for ex in curated_examples if not ex.outputs.get('is_available', True))
    positive_count = len(curated_examples) - negative_count
    
    # Analyze domain diversity for positive cases
    positive_examples = [ex for ex in curated_examples if ex.outputs.get('is_available', False)]
    domain_diversity = self._analyze_domain_diversity(positive_examples)
    unique_domains = len(domain_diversity)
    
    # Print comprehensive statistics
    console.print(f"[green]✓ Created curated dataset with {len(curated_examples)} examples[/green]")
    console.print(f"  - Negative examples (is_available: false): {negative_count} unique URLs")
    console.print(f"  - Positive examples (is_available: true): {positive_count} examples across {unique_domains} domains")
    console.print(f"  - Original dataset size: {len(original_examples)} examples")
    console.print(f"  - Curation ratio: {len(curated_examples)}/{len(original_examples)} ({100*len(curated_examples)/len(original_examples):.1f}%)")
```

## Testing Strategy

### Unit Test Coverage

#### Negative Case Extraction Tests
```python
class TestNegativeCaseExtraction:
    def test_extract_all_negative_examples(self):
        """Test that all negative examples are captured."""
        examples = [
            create_example("http://site1.com", is_available=False),
            create_example("http://site2.com", is_available=True),  
            create_example("http://site3.com", is_available=False),
        ]
        
        builder = DatasetBuilder(curation_enabled=True)
        negatives = builder._extract_negative_examples(examples)
        
        assert len(negatives) == 2
        assert all(not ex.outputs['is_available'] for ex in negatives)
    
    def test_negative_url_deduplication(self):
        """Test URL deduplication for negative examples."""
        examples = [
            create_example("http://site1.com", is_available=False, created_at="2025-01-01"),
            create_example("http://site1.com", is_available=False, created_at="2025-01-02"),  # More recent
            create_example("http://site2.com", is_available=False, created_at="2025-01-01"),
        ]
        
        builder = DatasetBuilder(curation_enabled=True)
        negatives = builder._extract_negative_examples(examples)
        
        assert len(negatives) == 2  # Deduplicated
        site1_example = next(ex for ex in negatives if 'site1.com' in ex.inputs['website_url'])
        assert site1_example.metadata['created_at'] == "2025-01-02"  # Most recent kept
```

#### Positive Case Selection Tests  
```python
class TestPositiveCaseSelection:
    def test_domain_diversity_optimization(self):
        """Test that positive selection maximizes domain diversity."""
        examples = [
            create_example("http://site1.com", is_available=True),
            create_example("http://site1.com/page", is_available=True),  # Same domain
            create_example("http://site2.com", is_available=True),
            create_example("http://site3.com", is_available=True),
        ]
        
        builder = DatasetBuilder(curation_enabled=True)
        positives = builder._select_representative_positive_examples(examples, target_count=3)
        
        domains = [builder._extract_domain(ex.inputs['website_url']) for ex in positives]
        assert len(set(domains)) == 3  # All different domains
    
    def test_quality_scoring_prioritization(self):
        """Test that higher quality examples are preferred."""
        examples = [
            create_example("http://site1.com", is_available=True, notes="Website accessibility status unclear"),  # Low quality
            create_example("http://site2.com", is_available=True, notes="Website accessible - content successfully scraped"),  # High quality
        ]
        
        builder = DatasetBuilder(curation_enabled=True)
        score1 = builder._calculate_quality_score(examples[0])
        score2 = builder._calculate_quality_score(examples[1])
        
        assert score2 > score1  # High quality scores higher
```

### Integration Test Coverage

#### End-to-End Curation Test
```python
class TestEndToEndCuration:
    @pytest.mark.asyncio
    async def test_curated_dataset_creation(self):
        """Test complete curated dataset creation workflow."""
        # Mock database with mixed availability examples
        mock_traces = create_mock_traces_with_mixed_availability(
            negative_count=5, positive_count=200, unique_domains=150
        )
        
        builder = DatasetBuilder(curation_enabled=True, database=mock_db)
        dataset = await builder.create_dataset_from_db(
            project="test-project",
            start_date="2025-01-01", 
            end_date="2025-01-01",
            eval_type="availability"
        )
        
        # Validate curation results
        assert len(dataset.examples) <= 100  # Size limit respected
        
        negative_examples = [ex for ex in dataset.examples if not ex.outputs['is_available']]
        assert len(negative_examples) == 5  # All negatives included
        
        # Check URL uniqueness
        urls = [ex.inputs['website_url'] for ex in dataset.examples]
        assert len(urls) == len(set(urls))  # No duplicates
```

### CLI Integration Tests
```python
def test_best_100_cli_parameter(runner):
    """Test --best-100 CLI parameter integration."""
    result = runner.invoke(create_dataset, [
        '--project', 'test-project',
        '--eval-type', 'availability', 
        '--date', '2025-01-01',
        '--best-100',
        '--output', 'curated.jsonl',
        '--name', 'test-curated'
    ])
    
    assert result.exit_code == 0
    assert "Created curated dataset" in result.output
    assert "Negative examples" in result.output
    assert "Positive examples" in result.output
    
def test_best_100_availability_only_restriction(runner):
    """Test that --best-100 only works with availability eval_type."""
    result = runner.invoke(create_dataset, [
        '--project', 'test-project',
        '--eval-type', 'token_name',  # Not availability
        '--date', '2025-01-01', 
        '--best-100',  # Should fail
        '--output', 'test.jsonl',
        '--name', 'test'
    ])
    
    assert result.exit_code == 1
    assert "only supported for --eval-type availability" in result.output
```

## Success Metrics

### Data Quality Metrics
- **100% Negative Coverage**: All `is_available: false` examples included in curated datasets
- **0% URL Duplication**: No duplicate website_urls across any curated dataset
- **>80% Domain Diversity**: Unique domains for positive cases when sufficient data available  
- **Target Size Achievement**: 100 examples achieved or clearly justified when not possible

### Performance Metrics
- **<10% Overhead**: Curation adds minimal time to dataset creation process
- **Memory Efficiency**: Large date ranges handled without memory pressure
- **Validation Coverage**: 100% of data quality issues caught by validation

### User Experience Metrics  
- **Clear Reporting**: Curation statistics provide complete insight into selection process
- **Predictable Results**: Same date range produces consistent curation results
- **Graceful Degradation**: Clear warnings when target size not achievable with available data

## Risk Assessment

### Technical Risks
1. **Performance Impact**: Curation logic might slow dataset creation for large date ranges
2. **Memory Usage**: Sorting and analyzing large datasets could cause memory issues
3. **Edge Case Handling**: Insufficient data scenarios might not be handled gracefully

### Data Quality Risks
1. **Bias Introduction**: Domain diversity optimization might introduce selection bias
2. **Quality Scoring Accuracy**: Quality scoring system might not reflect actual example value
3. **Negative Case Missing**: Edge cases might cause some negative examples to be missed

### Mitigation Strategies
1. **Performance Testing**: Benchmark curation with large datasets and optimize bottlenecks
2. **Memory Management**: Process examples in batches for large date ranges
3. **Comprehensive Testing**: Test all edge cases and unusual data distributions
4. **Quality Validation**: Manual review of initial curated datasets to validate selection logic

## File Modifications

### Primary Implementation Files
```
/lse/commands/eval.py:
  - Add --best-100 CLI parameter
  - Add parameter validation (availability eval_type only)
  - Pass curation flag to DatasetBuilder

/lse/evaluation.py:  
  - Add curation_enabled parameter to DatasetBuilder.__init__
  - Implement _curate_dataset() method
  - Implement _extract_negative_examples() with deduplication
  - Implement _select_representative_positive_examples() with domain diversity
  - Implement _calculate_quality_score() for positive example ranking
  - Implement _validate_curated_dataset() for quality assurance
  - Implement _print_curation_statistics() for detailed reporting
```

### Test Files
```
/tests/test_dataset_curation.py:
  - TestNegativeCaseExtraction class with comprehensive negative case tests
  - TestPositiveCaseSelection class with domain diversity and quality scoring tests
  - TestDatasetValidation class with uniqueness and completeness tests
  - TestCurationStatistics class with reporting accuracy tests

/tests/test_eval_command.py:
  - Integration tests for --best-100 CLI parameter
  - End-to-end curation workflow tests
  - Error handling tests for invalid parameter combinations
```

### Configuration Files
```
/tests/fixtures/curation_test_data.json:
  - Mock trace data with various availability scenarios
  - Mixed positive/negative examples across different domains
  - Edge case data for comprehensive testing
```

This comprehensive specification provides a detailed roadmap for implementing the `--best-100` feature with intelligent dataset curation, ensuring high-quality availability evaluation datasets with optimal balance and comprehensive test coverage.
