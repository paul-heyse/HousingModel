# Runbook: Innovation Jobs Metrics Refresh

## Purpose
Recompute innovation jobs metrics (location quotients, growth rates, migration, research awards, business formation) and persist them to the `market_jobs` table for market scoring and dashboards.

## Preconditions
- `.venv` activated with pandas, numpy, requests, and API client dependencies installed.
- Source API keys set (`AKER_BLS_API_KEY`, `AKER_CENSUS_API_KEY`, `AKER_NIH_API_KEY`, etc.).
- Data lake/cache writable; PostGIS database accessible.
- ETL feeds for jobs inputs refreshed (`runbooks/etl-pipelines.md`).

## Step-by-Step
1. **Fetch source datasets**
   ```bash
   python - <<'PY'
   from aker_jobs.sources import fetch_census_bfs, fetch_irs_migration

   bfs = fetch_census_bfs(state="08", start=2021, end=2023, measure="BFN")
   migration = fetch_irs_migration(year=2021, state="08")
   print(len(bfs), len(migration))
   PY
   ```
   Review counts; unexpected zeros indicate API or credential issues.
2. **Compute metrics**
   ```bash
   python - <<'PY'
   import pandas as pd
   from aker_jobs.metrics import location_quotient, migration_net_25_44

   naics = pd.read_parquet('data/jobs/denver_naics.parquet')  # From ETL output
   lq_df = location_quotient(
       naics,
       sector_column='sector',
       local_jobs_column='local_jobs',
       national_jobs_column='national_jobs',
       population_column='population',
       per_100k=True,
   )
   migration = pd.read_parquet('data/jobs/denver_migration.parquet')
   net_migration = migration_net_25_44(migration)
   print(lq_df.head())
   print(net_migration.mean())
   PY
   ```
   Update file paths to match ETL outputs for the target market.
3. **Persist to database**
   ```bash
   python - <<'PY'
   import pandas as pd
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_jobs.metrics import location_quotient, migration_net_25_44
   from aker_data.engine import create_engine_from_url
   from aker_data.models import MarketJobs

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   naics = pd.read_parquet('data/jobs/denver_naics.parquet')
   lq_df = location_quotient(
       naics,
       sector_column='sector',
       local_jobs_column='local_jobs',
       national_jobs_column='national_jobs',
       population_column='population',
       per_100k=True,
   )
   migration = pd.read_parquet('data/jobs/denver_migration.parquet')
   net_migration = migration_net_25_44(migration)

   job_record = MarketJobs(
       sba_id='DEN_202406',
       msa_id='DEN',
       data_vintage='2024-06-01',
       tech_lq=float(lq_df.loc[lq_df['sector'] == 'tech', 'lq'].iat[0]),
       health_lq=float(lq_df.loc[lq_df['sector'] == 'health', 'lq'].iat[0]),
       mig_25_44_per_1k=float(net_migration.iloc[0]),
       notes='Refreshed via jobs runbook 2024-06-04',
   )

   with Session() as session:
       session.merge(job_record)
       session.commit()
   PY
   ```
   Extend fields as additional metrics become available.
4. **Recompute market scores**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.markets.service import PillarScoreService
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   with Session() as session:
       service = PillarScoreService(session)
       service.refresh_one('DEN', as_of='2024-06-01')
   PY
   ```
   Confirms innovation pillar ingests refreshed metrics.
5. **Dashboard verification**
   - Launch GUI (`runbooks/gui-analytics.md`) and ensure Jobs/Innovation charts reflect updated figures.
   - Export Excel workbook and check Market_Scorecard innovation metrics.

## Validation
- `pytest tests/jobs/test_jobs_analysis.py tests/jobs/test_jobs_sources.py tests/jobs/test_jobs_validation.py`.
- `pytest tests/test_market_score_service.py` to confirm integration with market composer.
- SQL check:
   ```sql
   SELECT msa_id, data_vintage, tech_lq, mig_25_44_per_1k
   FROM market_jobs
   WHERE msa_id = 'DEN'
   ORDER BY data_vintage DESC
   LIMIT 5;
   ```

## Incident Response
- **API failures**: Inspect HTTP status, rotate API keys, retry with smaller date ranges.
- **Metric anomalies**: Validate ETL inputs; run summary stats to detect outliers before persisting.
- **Database constraint errors**: Ensure numeric columns within expected ranges; consult spec for acceptable bounds.

## References
- Capability brief: [capabilities/jobs-orchestration.md](../capabilities/jobs-orchestration.md)
- Spec: `openspec/specs/jobs/spec.md`
- ETL coordination: [runbooks/etl-pipelines.md](etl-pipelines.md)

