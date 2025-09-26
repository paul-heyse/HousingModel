## 1. Implementation
- [ ] 1.1 Create SQLAlchemy base and metadata with PostGIS/SpatiaLite dialect handling.
- [ ] 1.2 Implement ORM models under `src/aker_data/models/` for Markets and pillar tables plus supporting entities (scores, assets, runs, lineage).
- [ ] 1.3 Scaffold Alembic with env.py targeting the correct metadata; generate initial migration.
- [ ] 1.4 Add migration tests: upgrade from empty, downgrade to empty.
- [ ] 1.5 Add CRUD smoke tests for representative models, including a geometry column.
- [ ] 1.6 Document DSN patterns and dev setup (SpatiaLite activation).
