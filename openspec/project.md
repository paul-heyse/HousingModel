


This document is a **build spec** for a Python-based, production‑grade **Aker Property Model**. It translates your thesis and diligence checklists into a repeatable, auditable modeling system with a user‑friendly GUI, live data connectors, and one‑click exports to Excel, Word, and PDF.

---

# Project Context

## Purpose

Design and implement a **modular housing investment model** that:

* Scores **markets** (0–5) on Supply Constraints, Innovation Jobs, Urban Convenience, and Outdoor Access, with weights 30/30/20/20 and a separate **risk multiplier**.
* Evaluates **asset fit**, **deal archetypes**, **amenities & operations**, and **risk & resilience** against explicit guardrails.
* **Continuously ingests** fresh public and licensed datasets; **documents lineage**; produces **IC‑ready** scorecards and underwriting packets.
* Provides a **GUI for analysts** (no code) and a **Python SDK** for developers/automation.
* Outputs (a) **Excel** model configuration & results, (b) **Word** investment memos, (c) **PDF** reports.

## Tech Stack

* **Language & Core**

  * Python **3.12+**, Poetry, Pydantic v2, SQLAlchemy 2.x, GeoPandas/Shapely/pyproj/rtree
* **Storage & Geospatial**

  * PostgreSQL **+ PostGIS**, Parquet (data lake), SpatiaLite (dev)
* **APIs & ETL**

  * httpx/requests, **Prefect** (or Dagster) for orchestration, Great Expectations for data QA
* **Computation & Modeling**

  * NumPy/Pandas, scikit‑learn (robust scaling, winsorization), networkx/osmnx (walk/bike graphs)
* **GUI (Python‑native)**

  * **Dash** (Plotly Dash + dash‑leaflet), served by FastAPI/Uvicorn; Alt: **NiceGUI** (FastAPI‑native)
* **Services & Packaging**

  * FastAPI (REST), Pydantic Settings (12‑factor config), Uvicorn/Gunicorn
* **Exports**

  * xlsxwriter/openpyxl (Excel), **docxtpl** (Word), WeasyPrint or ReportLab (PDF)
* **DevEx / CI**

  * Ruff + Black + isort, mypy, pytest + pytest‑benchmark, pre‑commit, GitHub Actions

## Project Conventions

### Code Style

* **PEP‑8** with **Ruff** (lint) and **Black** (format); 120‑col line length.
* **Typing required** (mypy strict); Pydantic models as DTOs; NumPy docstrings.
* Module naming: `aker_<domain>` (e.g., `aker_market`, `aker_asset`); functions snake_case; classes PascalCase.

### Architecture Patterns

* **Clean Architecture + plugin architecture** for data connectors.
* **Hexagonal ports/adapters**:

  * Ports: `MarketScorer`, `AssetEvaluator`, `DealArchetypeModel`, `RiskEngine`.
  * Adapters: `CensusACSConnector`, `BLSConnector`, `OSMConnector`, etc.
* **Immutable inputs → deterministic outputs**; all runs persist config + hash.
* **Feature flags** via `pydantic-settings` and environment variables.
* **Geospatial first**: all sites and polygons stored in PostGIS; CRS standardized to EPSG:3857 (UI) and EPSG:4326 (storage).

### Testing Strategy

* **Unit**: function‑level tests for each metric.
* **Property‑based** (Hypothesis): score normalization monotonicity & bounds.
* **Golden‑master**: lock IC packet outputs for representative markets/sites.
* **Data QA** (Great Expectations): schema, ranges, joins, geographic coverage.
* **Performance**: benchmarks for 15‑min accessibility and OSM routing.
* **E2E**: GUI smoke tests with Playwright (Dash) + mocked APIs.

### Git Workflow

* **Trunk‑based** with short‑lived feature branches.
* **Conventional Commits** (`feat:`, `fix:`, `perf:`, `data:`, `chore:`).
* **PR gates**: tests + lint + type + data QA.
* **Release**: semantic versioning; changelog auto‑generated.

## Domain Context

Aker thesis = **supply‑constrained + innovation jobs + urban convenience + outdoor access**, operationalized via a **scorecard** and **guardrails** that feed underwriting and “Invest → Create → Operate” decisions. Western states (CO/UT/ID) receive additional **patterning** and hazard attention (hail, wildfire, snow load, water stress).

## Important Constraints

* **Auditability**: every score derived from versioned data and formulas; run metadata stored (data vintage, code commit, parameters).
* **Reproducibility**: deterministic; random seeds fixed; pure functions for metrics.
* **Licensing**: separate namespaces for public vs. licensed data; fallbacks required.
* **Performance**: state‑scale runs complete within target SLAs (e.g., <5 min per MSA for market scoring on standard cloud worker).
* **PII**: none required; adhere to provider T&Cs and rate limits.
* **Offline mode**: cached parquet & OSM extracts for travel.

## External Dependencies

**Public**: US Census/ACS & BFS, BLS (CES, QCEW), BEA, IRS migration, HUD, FHFA, FRED, NIH RePORTER, NSF Awards, DoD SBIR/STTR, OSM (POIs & network), TIGER/Line, EPA AirNow/NowCast, NOAA (HMS smoke, climate normals), USGS, FEMA NFHL, USFS/BLM, state parcels/permits, state wildfire polygons.
**Commercial (optional)**: CoStar/Costar permits, Zillow/Redfin rent/price series, SafeGraph/Placekey, Placer/StreetLight, Mapbox/Google basemaps.
**Tools**: OSRM/valhalla for routing (optional local containers).

---

#Model attributes to include#

Below each item you’ll find **Metrics**, **Data/Connectors**, **Computation**, **UI**, and **Schema**. All metrics are normalized to **0–100** (robust min‑max with winsorization) then mapped to a **0–5 pillar** via bucketing. Final market score = weighted average (**Supply 30% / Jobs 30% / Urban 20% / Outdoors 20%**). **Risk multipliers** adjust exit cap and contingencies.

---

## 1) Market fit (make these measurable)

### A. Supply‑constrained markets

* **Metrics**

  * *Topography & land*: % parcels with slope > 15°; % protected/public; waterway buffer area %; airport noise & view‑shed limits coverage.
  * *Regulatory friction*: median days application→permit→CO; presence of IZ; design review flag; height/FAR/parking minimum strictness; water hookup moratoria flag.
  * *Elasticity proxy*: **building permits / 1k households (3‑yr avg)** (inverse), **rental vacancy** (inverse), **time on market (MF lease‑ups)** (inverse).
* **Data/Connectors**

  * Local permit portals (scrapers/API), Census ACS (households), HUD vacancy, proprietary lease‑up (or construct from listings), parcels/slope (LiDAR/USGS DEM), OSM/TIGER, municipal code catalogs.
* **Computation**

  * Parcel‑level slope from DEM; buffers (100–300 ft) around water; zoning rules → categorical encodings; 3‑yr rolling averages for permits; vacancy/ToM trailing 4Q median.
* **UI**

  * Choropleth for constraints; “Reg friction” radar; elasticity gauge with tooltips showing data vintages.
* **Schema (tables)**

  * `market_supply(sba_id, slope_pct, protected_pct, buffer_pct, noise_overlay_pct, iz_flag, review_flag, height_idx, parking_idx, permit_per_1k, vacancy_rate, tom_days, v_intake)`.

### B. Innovations‑driven employment

* **Metrics**

  * 3‑yr **job growth** and **LQ** in **tech/health/edu/adv mfg**.
  * Announced expansions (counts & jobs) for universities/health/semis/defense.
  * Human capital: bachelor’s %, grad enrollment density, NIH/NSF/DoD awards per 100k, startup/business formation rate, **net in‑migration 25–44**.
* **Data**

  * BLS CES/QCEW by NAICS, BEA, NIH/NSF APIs, DoD SBIR, Census BFS, IRS/Census flows, IPEDS for enrollment, press/RSS ingestors for expansions (optional).
* **Computation**

  * Sector filters (NAICS lists), LQ = regional share / national share; CAGR(3y); normalize per 100k pop; migration = in‑minus out‑flows for 25–44.
* **UI**

  * Sector stackbars; expansion timeline; migration heatmap.
* **Schema**

  * `market_jobs(sba_id, tech_cagr, health_cagr, edu_cagr, mfg_cagr, tech_lq, ..., awards_per_100k, bfs_rate, mig_25_44_per_1k, expansions_ct, v_intake)`.

### C. Urban convenience

* **Metrics**

  * **15‑minute access** counts (walk & bike separately): grocery, pharmacy, K‑8, transit stop, urgent care; **intersection density**; **bikeway connectivity** index.
  * **Everyday retail health**: vacancy %, asking rent trend, daytime population within 1‑mile, last‑mile delivery coverage presence.
* **Data**

  * OSM POIs + osmnx networks; GTFS feeds; local retail datasets; SafeGraph/footfall (optional); carrier coverage for last‑mile (binary/proxy).
* **Computation**

  * Isochrone catchments (15 min @ 4.8 km/h walk; 15 min @ 15 km/h bike) via network shortest paths; count POIs; connectivity via giant component share & edge density; daytime pop via LODES/LEHD or proxy.
* **UI**

  * Isochrone map with POI hits; “15‑minute score” badge; trend sparkline for retail rents.
* **Schema**

  * `market_urban(sba_id, walk_15_ct, bike_15_ct, k8_ct, transit_ct, urgent_ct, interx_km2, bikeway_conn_idx, retail_vac, retail_rent_qoq, daytime_pop_1mi, lastmile_flag, v_intake)`.

### D. Outdoor recreation

* **Metrics**

  * Minutes to nearest **trailhead, ski bus, reservoir/river, regional park**; **trail miles per capita**; **public land % within 30‑min drive**.
  * **Air & noise**: PM2.5 seasonal variation; wildfire smoke days (rolling 3yr); proximity to highway/rail (inverse).
* **Data**

  * OSM trails & parks, USFS/BLM, regional transit GTFS, EPA AirNow, NOAA HMS smoke, DOT networks.
* **Computation**

  * Drive‑time matrix (OSRM/valhalla or network heuristics); per‑capita normalizations; AQ indices from daily PM2.5; smoke‑day counts.
* **UI**

  * Outdoor “badge rack” (mins to X); AQ seasonal chart.
* **Schema**

  * `market_outdoors(sba_id, min_trail_min, min_ski_bus_min, min_water_min, park_min, trail_mi_pc, public_land_30min_pct, pm25_var, smoke_days, hw_rail_prox_idx, v_intake)`.

**Pillar Aggregation & Weights**

* Normalize each metric to 0–100 (robust min‑max, winsor at 5th/95th).
* Pillar score = weighted mean of its metrics → map to **0–5** via quantile bins.
* **Market Score** = 0.3*Supply + 0.3*Jobs + 0.2*Urban + 0.2*Outdoors.
* **Risk factor** (0.90–1.10) stored separately and applied in underwriting.

---

## 2) Asset fit (what to buy/build)

* **Product types**: garden/low‑rise; select mid‑rise; **mixed‑use** with ground floor activation; selective adaptive reuse.
* **Vintage & scope**: 1985–2015 value‑add; **select ground‑up** infill/transit/outdoor gateways.
* **Unit mix bias**: studios/1BR near job cores; more **2BR/3BR** in family/WFH nodes; **in‑unit W/D** target.
* **Physical enablers**: balconies, **mudroom/gear nooks**, secure bike/ski storage, dog wash, **EV‑ready**.
* **Parking/transit**: 0.5–0.8 stalls/unit (infill), 1.1–1.4 (suburban); right‑size from observed car ownership & transit headways.

**Implementation**

* `asset_policy` guardrails: acceptable construction types, min ceiling height, min avg SF by unit type, parking ratio bands by context.
* UI **Asset Fit Wizard**: sliders & toggles produce **Fit Score** (0–100) and flags (“parking high vs target”, “no W/D”).
* Schema `asset_fit(asset_id, product_type, vintage_ok, unit_mix_fit, parking_fit, outdoor_enablers_ct, ev_ready_flag, adaptive_reuse_feasible_flag, fit_score)`.

---

## 3) Deal archetypes (how returns are created)

1. **Classic value‑add** (light–medium): interiors, common areas, brand uplift, access control, smart devices.
   *Modeled lift:* **+$90–$180/mo**; **payback < 4 yrs** interiors; retention +150–300 bps.

2. **Heavy lift / reposition**: systems/envelope, amenity re‑program, unit splits/mix rebalance; adaptive‑reuse potential.
   *Modeled lift:* blended (rents ↑, concessions ↓, reputation ↑); longer downtime buffer.

3. **Town‑center infill / small mixed‑use**: yield‑on‑cost vs stabilized cap spread; retail as **placemaking** (break‑even underwriting).

**Implementation**

* Library of **scope templates** with `cost_per_door`, `expected_lift`, `downtime_weeks`, `retention_delta`.
* ROI ranking = lift ($/mo) × duration / cost; enforce **payback thresholds**.
* Schema `deal_archetype(scope_id, name, cost, lift, payback_mo, downtime_wk, retention_bps, retail_underwrite_mode)`.

---

## 4) Amenity & programming (brand = NOI mechanics)

* **Remote‑work** (quiet rooms, micro‑offices, robust Wi‑Fi; membership revenue).
* **Outdoor life** (tune bench, boot dryers, maps, shuttle tie‑ins, group events).
* **Pet‑forward** (dog run + wash).
* **Events & partners (Aker “Collective”)**: track **CAC↓, lease‑up days↓, renewals↑**.
* **Sustainability that pays** (LED/controls, low‑flow/leak detection, envelope sealing; submetering; resident dashboards).

**Implementation**

* Amenity ROI model: `capex`, `opex`, `rent_premium`, `retention_delta`, `membership_rev`.
* KPI hooks in Ops dashboard: renewal %, review volume/rating, referral share.
* Schema `amenity_program(asset_id, amenity, capex, kpi_links, modeled_impact)`.

---

## 5) Operating model (Invest → Create → Operate drivers)

* **Fundamentals**: NPS loop → pricing/features; **reputation lift** reduces concessions & speeds lease.
* **Creative** (capex/dev): rank scopes by $/unit vs $/mo lift; stage to minimize vacancy.
* **Collective** (community): budget/door; KPIs → rent growth deltas.

**Implementation**

* Feedback ingestion (reviews/NPS) → **Reputation Index** → pricing guardrails.
* Renovation cadence optimizer (units/week) under vacancy cap.
* Schema `ops_model(asset_id, nps, reputation_idx, concession_days_saved, cadence_plan)`.

---

## 6) Risk & resilience (underwriting baked‑in)

* **Climate & insurance**: wildfire WUI, hail, snow load; deductible structures; parametric add‑ons.
* **Water stress**: impact fees, taps, drought plans; retrofit rebates.
* **Tax & policy**: reassessment cadence, appeals, rent control/just‑cause, STR spillovers.
* **Construction volatility**: winter premiums, logistics, labor.

**Implementation**

* **Risk multipliers** (0.90–1.10) by peril & policy → exit cap and contingencies.
* Schema `risk_profile(asset_or_market_id, peril, severity_idx, insurance_deductible, multiplier)`.

---

## 7) CO / UT / ID patterning (first‑pass guides)

* **CO**: aero/tech/health anchors; town‑center nodes; entitlement variance; **hail/wildfire** insurance.
* **UT**: tech/higher‑ed anchors; **topography‑driven supply friction**; water rights/winter timing.
* **ID**: in‑migration; small‑scale walkable districts; property‑tax dynamics; **forest‑interface wildfire**.

**Implementation**

* State rule packs (defaults, perils, winterization cost adders, tax cadence).
* UI: state selector → prefilled guardrails.

---

## 8) “Aker‑fit” diligence checklist (pre‑LOI)

**Market**: permits vs household growth; vacancy; sector job adds; 15‑min audit; trail/park distance.
**Site**: walk/bike/transit scores; micro‑retail health; school quality; noise/air; flood/wildfire; utility capacity/taps.
**Building**: envelope/systems (blower‑door/IR), leak history, roof/snow load, as‑builts variance.
**Financial/ops**: lead→lease funnel, renewal reasons, reputation diagnostics, controllables vs pass‑throughs, insurance loss runs.

**Implementation**

* Checklist UI with **auto‑populate** from data connectors; manual overrides logged with reason codes.

---

## 9) Scorecard schema (drop‑in)

| Pillar            | Weight | Example metrics (normalized 0–100)                                                    |
| ----------------- | -----: | ------------------------------------------------------------------------------------- |
| Supply Constraint |    30% | Permits/1k HH (inv.), entitlement days (inv.), vacancy (inv.), protected/steep land % |
| Innovation Jobs   |    30% | 3‑yr sector job CAGR, LQ in tech/health/edu/mfg, 25–44 net migration                  |
| Urban Convenience |    20% | Amenity within 15‑min count, intersection density, transit headways                   |
| Outdoor Access    |    20% | Minutes to trailhead/park/water, trail miles per capita, air‑quality days             |

**Risk multipliers**: insurance + tax + water/entitlement (0.90–1.10) applied to cap/exit & contingency.

---

## 10) Quick “non‑fit” tells

* Elastic greenfield sprawl, easy entitlements, high supply elasticity.
* Auto‑only sites, far from daily needs; weak outdoor access.
* Hard rent caps (for value‑add) unless basis exceptional.
* Chronic envelope failures without finite fix path.

---

# Additional implementation details

## Data connectors (examples & refresh)

* **Census/ACS, BLS, BEA, LEHD/LODES, BFS, IRS migration, NIH/NSF/DoD**, **OSM/GTFS**, **EPA/NOAA/USGS/FEMA**, **state parcels/permits**.
* **Refresh cadence** per source (daily/weekly/monthly/annual); ETag/Last‑Modified respected; **data_vintage** logged per table.

## Normalization & scoring (pseudocode)

```python
def robust_minmax(x, p_low=0.05, p_high=0.95):
    lo, hi = np.quantile(x[~np.isnan(x)], [p_low, p_high])
    x_clipped = np.clip(x, lo, hi)
    return 100 * (x_clipped - lo) / max(hi - lo, 1e-9)

def pillar_score(metrics: dict[str, float], weights: dict[str, float]) -> float:
    # metrics already 0–100
    wsum = sum(weights.values())
    return sum(metrics[k]*weights[k] for k in weights) / wsum

def to_five_bucket(pillar_0_100: float) -> float:
    # 0–5 in 0.5 increments by quantiles (precomputed per market set)
    return np.digitize(pillar_0_100, [20, 40, 60, 80])  # 0..4 → map to 0..5
```

## Excel / Word / PDF exports

* **Excel**: single workbook with sheets:

  * `Overview`, `Market_Scorecard`, `Asset_Fit`, `Deal_Archetypes`, `Risk`, `Ops_KPIs`, `CO-UT-ID_Patterns`, `Checklist`, `Data_Lineage`, `Config`.
* **Word**: `docxtpl` templates with placeholders (e.g., `{{ msa_name }}`, tables for metrics); charts inserted as PNGs.
* **PDF**: either render the Word doc via a converter or produce HTML+CSS → PDF via WeasyPrint; include appendix with data sources and vintages.
* **CLI**: `aker report --msa=BOI --asset=Foo --as-of=2025-09-01 --format=pdf`.

## GUI (Dash) pages

1. **Market Scorecard**: map + pillar cards + data vintage banner; export buttons.
2. **Deal Workspace**: select archetype, scope stack, ROI ladder, downtime schedule.
3. **Asset Fit Wizard**: guided checklist with live fit score and guardrail flags.
4. **Risk Panel**: WUI/hail/snow maps, insurance scenarios, multipliers.
5. **Ops & Brand**: NPS & review ingestion, reputation→pricing rules.
6. **Data Refresh**: source toggles, last‑run logs, lineage drilldown.
7. **CO/UT/ID Patterning**: pre‑filled defaults & hazards.

## Database schema (high‑level)

* `markets (msa_id, name, geo, pop, households, data_vintage)`
* `market_supply / market_jobs / market_urban / market_outdoors` (as above)
* `pillar_scores (msa_id, supply_0_5, jobs_0_5, urban_0_5, outdoor_0_5, weighted_0_5, risk_multiplier, run_id)`
* `assets (asset_id, msa_id, geo, year_built, units, product_type, ...)`
* `asset_fit, deal_archetype, amenity_program, risk_profile, ops_model`
* `runs (run_id, git_sha, config_json, created_at)`
* `lineage (table, source, source_url, fetched_at, hash)`

## Security & secrets

* `.env` or cloud secret store; **no secrets in code**.
* Rate limiting and backoff; retry with jitter; circuit breaker per source.

---

#additional requirements list#


## 1) Mandate & return targets

* **Implement**: `mandate.yml` + `Mandate` table; hard guards in underwriting.
* **Fields**: strategy bands, check sizes, market/asset exposure caps, target IRR/EM, CoC, YoC vs exit cap spread, DSCR min, hold horizon, fees/promote (for reporting).

## 2) Portfolio construction & concentration limits

* **Implement**: Portfolio dashboard with exposure dials + alerts.
* **Fields**: by strategy/state/MSA/submarket/vintage/construction/rent band; correlation notes; pacing plan.

## 3) Geography precision

* **Implement**: ranked **MSA/submarket leaderboard**; no‑go polygons.
* **Fields**: min MF stock, absorption, replacement cost, broker coverage; avoidance zones (floodplain, WUI high, water moratoria).

## 4) Negative screens

* **Implement**: exclusion lists enforced in UI and SDK.
* **Fields**: product types, policy screens, physical/site screens with thresholds.

## 5) Product specification

* **Implement**: standards matrix per product type.
* **Fields**: vintage bands, construction class, unit mix ranges, min avg SF, ceiling heights, W/D required, parking policy, ADA retrofit stance, digital infra spec.

## 6) Resident segment & rent band

* **Implement**: affordability positioning & comp‑set protocol.
* **Fields**: target rent‑to‑income, income bands, expected HH size, WFH share, comp rent premium goal, pet policy.

## 7) Acquisition underwriting guardrails

* **Implement**: pre‑IC guardrail checks with pass/fail.
* **Fields**: bad debt/concession caps, basis vs replacement, expense sanity (tax/ins/util escalators), break‑even occupancy, sensitivity grid templates, contingencies.

## 8) Value‑add scope & economics

* **Implement**: scope library with **test‑batch** flag.
* **Fields**: light/med/heavy menu, cost/door, expected lift/door, payback, downtime cadence.

## 9) Development criteria

* **Implement**: dev underwrite module.
* **Fields**: YoC mins, margin targets, spread to cap, land basis guardrails, density/FAR, parking by transit, schedule milestones, pre‑leasing, absorption, procurement, envelope/MEP standards (snow/wind/radon).

## 10) Capital structure & rate strategy

* **Implement**: capital stack builder; hedging policy.
* **Fields**: leverage bands, fixed/float mix, cap/swap rules, recourse, covenants, lender type, mezz/pref policy.

## 11) Insurance & risk transfer

* **Implement**: insurance program model.
* **Fields**: program structure, deductibles, named peril treatment, builders risk, GL/umbrella, cyber/crime/environmental, captive feasibility.

## 12) Climate, water, resilience

* **Implement**: resilience checklist & cost adders.
* **Fields**: WUI thresholds, defensible space, ignition‑resistant materials, water taps/fees/drought stages, low‑flow targets, AQ/smoke response, backup power, freeze/flood/snow ops.

## 13) ESG goals & reporting

* **Implement**: ESG register + targets.
* **Fields**: energy/water intensity targets, carbon stance, renewables readiness, certifications (ENERGY STAR/Fitwel/NGBS), GRESB policy, data capture stack, materials & waste diversion metrics.

## 14) Operations model

* **Implement**: PM SLAs & staffing calculator; revenue management rules.
* **Fields**: workorder SLA, make‑ready days, first‑contact resolution, units/FTE, on‑site vs roving, pricing tool guardrails, utilities (RUBS/submeter), vendor programs, PM schedules, resident insurance compliance.

## 15) Community & brand programming (Collective)

* **Implement**: program budget/door; event cadence; KPI wiring.
* **Fields**: NPS target, review volume/rating, referral %, renewal delta, lead‑to‑lease conversion, CAC reduction; signage/naming standards.

## 16) Marketing & leasing

* **Implement**: channel mix & CAC benchmarks; tour strategy; CRM hooks.
* **Fields**: ILS/SEO/social/referral/broker split, self‑guided vs staffed, attribution, pre‑leasing playbook, reputation cadence.

## 17) Compliance & legal

* **Implement**: Fair Housing/ADA workflows; landlord‑tenant rules registry.
* **Fields**: notices/fees/deposits, eviction/delinquency policy, contract assignability, labor/union flags, environmental protocols (Phase I/II, radon/asbestos/lead).

## 18) Diligence checklists

* **Implement**: deal + entity checklists with attachments.
* **Fields**: PCI/roof/envelope/sewer, lease file audits, revenue rec, tax appeals, loss runs, work‑order backlog, resident satisfaction baseline, vendor risks, title/zoning/special districts.

## 19) Data, tooling, governance

* **Implement**: data warehouse, definitions catalog, joins library, QA playbooks.
* **Fields**: metric definitions (vacancy, economic occ, LTL), joins across BLS/BEA/ACS/permits/OSM/parks/FEMA/wildfire/tax/comps; audit/version control for models.

## 20) CO/UT/ID operating notes

* **Implement**: state ops packs.
* **Fields**: water/taps, winterization, irrigation shares, hail exposure & roofing materials, wildfire smoke protocols, radon mitigation, tax quirks & protest strategies.

## 21) Exit strategy & disposition

* **Implement**: exit lanes & readiness checklist.
* **Fields**: sale/roll‑up/recap/refi/condo‑map, docs/warranties/T‑12 hygiene, lease audit pack, broker selection/comp.

## 22) Governance & decisioning

* **Implement**: IC workflow in app.
* **Fields**: IC composition/quorum, gated artifacts (Screen→IOI→LOI→IC1→IC2→Close), risk/ESG committee charters.

## 23) Investor relations & reporting

* **Implement**: reporting cadence & package builder.
* **Fields**: quarterly deck, KPI tables, ESG metrics, valuation policy, independent marks, LPAC/co‑invest rights.

## 24) Tax planning

* **Implement**: tax benefit modeler.
* **Fields**: cost seg/bonus dep, 45L/179D, 1031/UPREIT options, FIRPTA/UBTI handling, construction sales tax by state.

## 25) Security, life‑safety & wellbeing

* **Implement**: CPTED & access control standards; emergency plans.
* **Fields**: lighting/camera coverage, access hierarchy, emergency comms, IEQ (ventilation, moisture/mold, CO/CO₂).

#second additional requirements list#

#additional considerations (Implementation Spec)#

> This section is designed to **drop into** the document you already started. Each consideration is expressed using the same spec style as before, with **Implement**, **Fields/Guards**, **Computation/Logic**, **UI & Exports**, and **Schema** blocks so devs and AIs can build directly.

---

## 1) Capital & hurdle context (net, decision‑ready outputs)

* **Implement**

  * Net‑of‑fees **cash‑flow translator** and **waterfall engine** (multi‑tier promote).
  * Hurdle checks for **YoC–exit‑cap spread** and **stabilized CoC**.
* **Fields/Guards**

  * `target_net_irr`, `target_em`, `hold_years`, `fees_{acq,am,disp,dev}`, `promote_tiers`, `required_spread_bps`, `stabilized_coc_min`.
* **Computation/Logic**

  * Convert **gross → net to equity**: subtract fees, AM draws, promote per tier; compute IRR/EM/CoC.
  * Gate: fail if `(YoC – ExitCap) < required_spread_bps` or `CoC < min`.
* **UI & Exports**

  * Hurdle badge; “Gross vs Net” waterfall chart; Word/Excel “Net Summary” table.
* **Schema**

  * `mandate(capital_id, target_net_irr, target_em, hold_years, fee_sched_json, promote_json)`
  * `deal_hurdles(deal_id, yoc, exit_cap, spread_bps, coc_stab, passes)`

---

## 2) Portfolio construction guardrails (stay within mandate)

* **Implement**

  * Exposure caps by **MSA/submarket, vintage, construction, rent band, strategy** with **pre/post‑deal** deltas.
  * **Pacing tracker** for deployment vs dry powder.
* **Fields/Guards**

  * `cap_{msa,submkt,vintage,construct,rent_band,strategy}`, `pacing_target_$`, `dry_powder_$`.
* **Computation/Logic**

  * Compute exposures before/after; hard‑block if any cap exceeded; update pacing burn‑down.
* **UI & Exports**

  * “Exposure Dials” with **pre→post** arrows; IC one‑pager with cap headrooms.
* **Schema**

  * `portfolio_caps(dim, cap_pct_or_$)`
  * `portfolio_exposure(as_of, dim, value_pct_or_$)`
  * `pacing(as_of, target_$, actual_$, headroom_$)`

---

## 3) Market scorecard upgrades (from pillars to levers)

* **Implement**

  * Extend market metrics for **entitlement speed, taps/water, hazards (WUI/wildfire/hail/radon), amenities (15‑min), permits/1k HH, vacancy/absorption, insurance/tax regimes**.
  * Map score → **rent‑growth bands, absorption curves, exit‑cap adj, contingency multipliers**.
* **Fields/Guards**

  * `entitlement_days`, `tap_constraints_idx`, `hazard_idx`, `amenity15_idx`, `permits_per_1k`, `vacancy_%`, `absorption_rate`, `ins_regime`, `tax_regime`.
  * `rent_growth_band`, `absorption_curve_id`, `exit_cap_adj_bps`, `contingency_mult`.
* **Computation/Logic**

  * Deterministic **score→assumption** lookup tables with quantile mapping and state overrides.
* **UI & Exports**

  * “Assumption Deriver” panel shows how score feeds rent/exit/contingency.
* **Schema**

  * Extend `market_supply/jobs/urban/outdoors` + `market_regimes(msa_id, ins_regime, tax_regime, entitlement_days, tap_idx, hazards_json)`
  * `market_assumption_maps(version, score_range, rent_band, exit_cap_adj_bps, contingency_mult)`

---

## 4) Asset screening & basis tests (buy right)

* **Implement**

  * Hard screens for **DSCR, LTV/LTC, break‑even occ, YoC**.
  * Basis sanity vs **replacement cost** and **comp band**; require sensitivity grid.
* **Fields/Guards**

  * `dscr_min`, `ltv_max`, `ltc_max`, `be_occ_max`, `yoc_min`, `basis_vs_replacement_max`, `basis_vs_comp_band_max`.
* **Computation/Logic**

  * Auto‑pull replacement cost & comp band; flag **hard‑fail** without credible scope.
* **UI & Exports**

  * Red/green screen list; “Why failed” tooltips; sensitivity grid in Excel.
* **Schema**

  * `asset_basis_tests(deal_id, dscr, ltv, ltc, be_occ, yoc, basis_vs_repl, basis_vs_comp, passes)`

---

## 5) Value‑add economics (quantified “Creative” levers)

* **Implement**

  * Pre‑load scopes (light/med/heavy interiors; common‑area/amenities).
  * Compute **payback, ROI, retention uplift**; schedule to minimize vacancy.
* **Fields/Guards**

  * `scope{name, cost_per_unit, rent_lift, downtime_wk, retention_bps, common_area_cost, amenity_rev}`, `payback_max_months`.
* **Computation/Logic**

  * ROI ladder sort; cadence optimizer under vacancy cap; POC batch option.
* **UI & Exports**

  * Scope ROI ladder; cadence Gantt; “With/Without” NOI delta.
* **Schema**

  * `reno_scopes(scope_id, type, cost_per_unit, expected_lift, downtime_wk, retention_bps)`
  * `reno_plan(deal_id, scope_id, units, schedule_json, payback_mo, roi)`

---

## 6) Development underwriting (infill/mixed‑use)

* **Implement**

  * Thresholds for **YoC, dev margin**, **land basis**, schedule segments, tap fees, escalation, **winter premiums**, contract strategy (GMP/cost‑plus).
  * Interest carry & contingency tied to **schedule risk**; **pre‑leasing/absorption** tied to market score.
* **Fields/Guards**

  * `yoc_min`, `dev_margin_min`, `land_basis_max`, `tap_fee_$`, `esc_%`, `winter_prem_%`, `contract_type`, `prelease_target`, `absorption_curve_id`.
* **Computation/Logic**

  * Schedule Monte Carlo (triangular/PERT) feeds carry & contingency; rent up via chosen curve.
* **UI & Exports**

  * Dev timeline; cost stack with risk adders; pre‑leasing dial.
* **Schema**

  * `development_underwrite(deal_id, yoc, margin, land_basis, schedule_json, carry_$, contingency_$, contract_type)`

---

## 7) Operations & pricing engine (Operate → NOI)

* **Implement**

  * Parameterize **PM fees, staffing, make‑ready days/cost, concessions, bad debt**, **revenue‑management guardrails**; utilities (RUBS/submeter); **preventive maintenance** cadence.
* **Fields/Guards**

  * `pm_fee_%`, `units_per_fte`, `make_ready_days`, `make_ready_cost`, `concession_policy`, `bad_debt_%`, `rev_mgmt_on`, `rev_mgmt_bands`, `utilities_mode`, `pm_schedule_json`.
* **Computation/Logic**

  * Dynamic **effective rent** per guardrails; opex impacts from staffing & PM cadence.
* **UI & Exports**

  * Pricing guardrail panel; “Ops to NOI” bridge chart.
* **Schema**

  * `ops_pricing(asset_id, params_json, effective_rent, opex_$, occupancy_assumed)`

---

## 8) Ancillary revenue & the “Collective” (brand → cash)

* **Implement**

  * Program budget/door that drives **renewal uplift, CAC↓, concession↓**, and ancillary income (parking, storage, pet, furnished, micro‑office).
  * Conservative/optimistic **toggles**.
* **Fields/Guards**

  * `program_budget_per_door`, `renewal_uplift_bps`, `cac_reduction_%`, `concession_reduction_%`, `ancillary_streams_json`, `scenario_mode`.
* **Computation/Logic**

  * Translate KPI shifts → **vacancy/marketing/concession** deltas; compute payback.
* **UI & Exports**

  * Program ROI card; “With/Without Collective” switch in IC packet.
* **Schema**

  * `ancillary_programs(asset_id, budget_per_door, kpi_impacts_json, ancillary_rev_$, payback_mo)`

---

## 9) Taxes, insurance & climate risk (Mountain‑West realities)

* **Implement**

  * Tax **reassessment logic**, appeal odds, special districts/abatements.
  * Insurance by **peril** with **premium + deductible + expected loss reserve**; high‑risk adds **exit‑cap premium**.
* **Fields/Guards**

  * `tax_reassess_rule`, `appeal_prob`, `special_districts`, `abatements`, `ins_{hail,wildfire,flood}_premium`, `deductibles_json`, `elr_%`, `exit_cap_premium_bps`.
* **Computation/Logic**

  * Year‑by‑year tax forecast; ELR accrual; exit‑cap bump where risk>threshold.
* **UI & Exports**

  * Tax glidepath chart; Insurance peril stack; risk→exit cap note.
* **Schema**

  * `tax_insurance(asset_or_msa, tax_model_json, ins_perils_json, elr_% , exit_cap_adj_bps)`

---

## 10) Debt, hedging & covenants (financing that sizes)

* **Implement**

  * Size debt off **DSCR/LTV/LTC** using **SOFR forward**; price **rate caps** (strike/tenor/premium).
  * Track covenants & headroom; **refi triggers** and cap replacement.
  * Reflect **recourse/lockboxes** in cash availability.
* **Fields/Guards**

  * `sofr_curve_id`, `amort_years`, `io_months`, `cap_strike`, `cap_tenor`, `cap_premium`, `dscr_min`, `ltv_max`, `ltc_max`, `recourse_flag`, `lockbox_type`.
* **Computation/Logic**

  * Debt sizing solves for lower of DSCR/LTV/LTC; covenant time‑series; refi scenario engine.
* **UI & Exports**

  * Debt sizing worksheet; covenant headroom timeline; cap pricing card.
* **Schema**

  * `debt_stack(deal_id, tranche_id, terms_json, proceeds_$, covenants_json, headroom_ts)`
  * `hedges(deal_id, type, strike, tenor_mo, premium_$)`

---

## 11) Compliance & local policy (rules that gate rent/timing)

* **Implement**

  * Switches for **rent control/just‑cause**, **inclusionary/set‑asides**, **ADA remediation**, **eviction timelines**.
  * Apply caps/lag/capex‑opex impacts.
* **Fields/Guards**

  * `rent_cap_%`, `just_cause_flag`, `iz_set_aside_%`, `ada_scope_$`, `eviction_days`, `compliance_opex_$`.
* **Computation/Logic**

  * Cap rent growth; lengthen cash lag; add compliance costs on schedule.
* **UI & Exports**

  * Policy panel; compliance checklist with auto‑populated items.
* **Schema**

  * `policy_switches(msa_or_asset, params_json, effective_date)`

---

## 12) Exit, refi & disposition planning (how you get paid)

* **Implement**

  * Exit cap from **market evidence + scorecard risk adj**; sale costs; **refi‑then‑hold** option.
  * Sensitize exit timing to lease‑up/stabilization & market regimes.
* **Fields/Guards**

  * `exit_cap_base`, `exit_cap_adj_bps`, `sale_cost_%`, `refi_option_on`, `exit_timing_rule`.
* **Computation/Logic**

  * Two‑lane outcomes (sell vs refi); NPV/IRR compare; timing windows.
* **UI & Exports**

  * Exit vs Refi toggle; proceeds waterfall table (Excel/Word).
* **Schema**

  * `exit_strategy(deal_id, mode, exit_cap, sale_cost_%, refi_terms_json, timing_rule)`

---

## 13) Scenario & sensitivity framework (decision confidence)

* **Implement**

  * **Downside/Base/Upside** scenario sets moving **rents, exit cap, ins/tax, reno cost & lift, schedule slip, absorption, interest**.
  * Aker‑specific lever: **Fundamentals/Collective ON/OFF**.
* **Fields/Guards**

  * `scenario_set_id`, `rent_delta_%`, `exit_cap_delta_bps`, `ins_tax_delta_%`, `reno_cost_delta_%`, `reno_lift_delta_%`, `schedule_slip_%`, `absorption_mult`, `rate_shift_bps`, `collective_on`.
* **Computation/Logic**

  * Batch run scenarios; present IRR/EM distribution + key driver tornado.
* **UI & Exports**

  * Scenario selector; tornado chart; 3‑case table printable for IC.
* **Schema**

  * `scenario_sets(set_id, params_json)`
  * `scenario_results(deal_id, set_id, irr_net, em, npv, key_drivers_json)`

---

## 14) State‑specific risk premia (CO / UT / ID)

* **Implement**

  * Encode **tap constraints, radon mitigation, hail belts, WUI overlays, winter scheduling** into cost, insurance, contingency, and exit‑cap by state/submarket.
* **Fields/Guards**

  * `state_pack_id`, `tap_fee_policy`, `radon_mitigation_$`, `hail_deductible_policy`, `wui_flag`, `winter_sched_adders_%`, `exit_premia_bps`.
* **Computation/Logic**

  * Auto‑apply pack by geo; override per asset.
* **UI & Exports**

  * State pack banner with applied adders; appendix note for IC.
* **Schema**

  * `state_premia(state, submarket, params_json)`

---

## 15) Timing & approvals (carry you can’t ignore)

* **Implement**

  * Probability‑weighted durations for **IC gates, entitlement, permits, utility letters, lender close** → float **interest carry** and start of cash flows.
* **Fields/Guards**

  * `gate{screen,ioi,loi,ic1,ic2}_days_dist`, `entitlement_days_dist`, `permit_days_dist`, `utility_letter_days_dist`, `lender_close_days_dist`.
* **Computation/Logic**

  * PERT/triangular per segment; critical‑path carry; display expected & p90 schedules.
* **UI & Exports**

  * Timeline with uncertainty bands; “cost of delay” metric.
* **Schema**

  * `timelines(deal_id, segment, dist_params_json, expected_days, p90_days, carry_cost_$)`

---

## 16) Track‑record calibration (priors keep you honest)

* **Implement**

  * Seed defaults from **realized projects** for lift/$, downtime, lease‑up velocity, schedule slip, cost variance.
* **Fields/Guards**

  * `prior_{lift_per_$, downtime_wk, leaseup_v, schedule_slip_%, cost_var_%}`, `credence_weight_%`.
* **Computation/Logic**

  * Bayesian blend: `assumption = prior*w + observed*(1-w)`.
* **UI & Exports**

  * “House vs Deal” assumptions diff; calibration panel.
* **Schema**

  * `track_record(metric, value, context_json, updated_at)`
  * `calibration(deal_id, metric, prior, observed, weight, blended)`

---

## 17) Data plumbing & definitions (comparability)

* **Implement**

  * **Definitions dictionary** (NOI, economic vs physical occ, LTL, capex vs opex), input provenance registry, and **locked formulas** for policy (e.g., reassessment rules).
* **Fields/Guards**

  * `definition_id`, `formula_locked`, `provenance(source, vintage, method)`.
* **Computation/Logic**

  * Enforce via validation; CI check to prevent formula drift.
* **UI & Exports**

  * Data lineage sidebar; Definitions appendix auto‑generated in Word/PDF.
* **Schema**

  * `definitions(def_id, name, text, formula, locked_bool)`
  * `provenance(table, source, vintage, method, hash)`

---

## 18) Portfolio‑level outputs (beyond the single deal)

* **Implement**

  * Roll‑up view of **exposure, leverage, hedge coverage, vintage mix** with approval ties to limits.
  * Automated “Great deal, wrong bucket” verdict.
* **Fields/Guards**

  * `post_deal_{exposure, leverage, hedge, vintage}`, `limit_breaches`, `approval_recommendation`.
* **Computation/Logic**

  * Simulate portfolio after adding deal; compute delta vs caps; produce decision text.
* **UI & Exports**

  * Portfolio shift waterfall; hedge coverage chart; IC cover slide.
* **Schema**

  * `portfolio_rollup(run_id, before_json, after_json, verdict, notes)`


### Integration Notes

* These modules **hook directly** into the existing **Market/Asset/Deal/Risk** tables and GUI pages you defined earlier.
* Keep all new assumptions **versioned**; surface **data vintage** + **assumption pack** in every export (Excel/Word/PDF) so ICs see **what moved** and **why**.
