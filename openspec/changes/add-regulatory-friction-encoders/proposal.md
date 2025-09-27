## Why

The Aker Property Model requires a comprehensive regulatory friction encoding system to quantify zoning and entitlement risks that significantly impact development feasibility and investment returns. Currently, regulatory constraints are handled inconsistently across markets, leaving critical entitlement risks unquantified in the scoring pipeline. A structured encoding system will provide normative, auditable assessments of inclusionary zoning strictness, design review requirements, height/FAR limitations, parking mandates, and water availability constraints - enabling consistent deal screening and risk-adjusted underwriting across all markets.

## What Changes

- **ADD** `aker_market.regulatory.encode_rules()` function for parsing municipal codes, zoning ordinances, and policy documents
- **ADD** structured encoding system for regulatory friction factors with normalized indices (0-100) and boolean flags
- **ADD** comprehensive zoning rule parser supporting multiple input formats (text, tables, PDFs)
- **ADD** database schema for storing regulatory friction metrics with MSA-level granularity
- **ADD** validation framework against manually curated truth sets for representative fixture cities
- **ADD** integration with market scoring pipeline for risk-adjusted supply constraint calculations
- **ADD** export functionality for regulatory data in Excel/Word investment memos
- **ADD** comprehensive test suite with regression testing against fixture cities
- **ADD** performance optimizations for large-scale regulatory document processing
- **BREAKING**: None - new capability extending market analysis without disrupting existing functionality

## Impact

- **Affected specs**: Market analysis capability, database schema, scoring integration
- **Affected code**: `src/aker_market/regulatory/`, `src/aker_market/database/`, `src/aker_market/scoring/`, `tests/aker_market/test_regulatory.py`
- **Dependencies**: Natural language processing libraries (spaCy, NLTK), PDF parsing (PyPDF2), SQLAlchemy for database integration, pandas for data processing
- **Risk**: High - regulatory interpretation requires domain expertise and careful validation against legal sources
- **Performance**: Optimized for batch processing of municipal codes with intelligent caching
- **Scalability**: Designed to handle all US MSAs with efficient document processing and storage
