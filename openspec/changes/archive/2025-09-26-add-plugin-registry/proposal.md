## Why
The platform needs a formal plugin system to support pluggable data connectors and calculators across market, asset, deal, and risk workflows. Without it, teams cannot swap adapters for testing or introduce new providers without touching core logic.

## What Changes
- Define port interfaces (`MarketScorer`, `AssetEvaluator`, `DealArchetypeModel`, `RiskEngine`) under `aker_core.ports`.
- Implement a plugin registry in `aker_core.plugins` that supports `register()`, `get()`, and entry-point based discovery for adapters like `CensusACSConnector`.
- Provide testing utilities to hot-swap adapters and validate discovery, ensuring the architecture remains hexagonal.

## Impact
- Affected specs: core
- Affected code: `aker_core/ports.py`, `aker_core/plugins.py`, test helpers for mocking connectors.
