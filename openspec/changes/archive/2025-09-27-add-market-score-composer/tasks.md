## 1. Specification
- [x] 1.1 Enhanced spec delta with detailed weighting scheme and validation requirements.

## 2. Implementation
- [x] 2.1 Implement `markets.score(msa_id|msa_geo, as_of)` returning `MarketPillarScores` with 0–5 and 0–100 fields.
- [x] 2.2 Add configurable weight overrides for scenario analysis and sensitivity testing.
- [x] 2.3 Update pillar_scores persistence for composite scores, metadata, and audit trails.
- [x] 2.4 Create standardized output format supporting both 0–5 and 0–100 variants.
- [x] 2.5 Add deterministic computation with fixed input regression tests.
- [x] 2.6 Implement pillar weight swap testing for sensitivity analysis.

## 3. Integration
- [x] 3.1 Integrate with existing pillar calculation pipelines (supply, jobs, urban, outdoors).
- [x] 3.2 Add support for MSA boundary resolution from geographic inputs.
- [x] 3.3 Create batch processing capabilities for multiple MSA scoring.
- [x] 3.4 Add performance optimization for large-scale market analysis.

## 4. Validation & Testing
- [x] 4.1 Run comprehensive pytest suite for deterministic behavior.
- [x] 4.2 Add pillar weight swap regression tests for sensitivity validation.
- [x] 4.3 Integrate with Great Expectations for pillar data validation.
- [x] 4.4 Create golden master tests with known input/output pairs.
- [x] 4.5 Add performance benchmarks for scoring computation.

## 5. Documentation & Deployment
- [x] 5.1 Document weight scheme, override behavior, and API surface.
- [x] 5.2 Update analytics dashboards to consume new composer output.
- [x] 5.3 Create deployment configurations for production scoring.
- [x] 5.4 Add monitoring and alerting for scoring pipeline health.
