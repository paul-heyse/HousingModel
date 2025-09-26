## Why
Data quality is critical for reliable analytics and decision-making. Without systematic validation, data corruption, missing values, or format inconsistencies can lead to incorrect business insights. Great Expectations provides a robust framework for defining and enforcing data quality expectations, ensuring data reliability throughout the ETL pipeline.

## What Changes
- Introduce Great Expectations suites for comprehensive data validation across all datasets.
- Create YAML-based expectation configurations for schema, range, join, and coverage checks.
- Integrate validation tasks into Prefect flows for automated quality assurance.
- Implement CI/CD gates that fail on expectation breaches.
- Provide monitoring and alerting for data quality issues.

## Impact
- Affected specs: etl/quality
- Affected code: `ge_suites/`, Prefect flow tasks, CI/CD pipelines, data quality monitoring.
