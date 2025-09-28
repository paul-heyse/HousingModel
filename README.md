# Aker Property Model

A comprehensive housing investment analysis and portfolio management platform that provides market scoring, deal evaluation, asset fit analysis, and automated portfolio monitoring with real-time dashboards and export capabilities.

## 🏗️ Architecture Overview

The Aker Property Model is built with a modular, domain-driven architecture featuring:

- **GUI Layer**: FastAPI + Dash web interface with 8 interactive dashboards
- **Service Layer**: Specialized modules for markets, assets, deals, and portfolio management
- **Core Infrastructure**: Configuration, logging, database, caching, and validation
- **Data Layer**: External API integration, ETL pipelines, and data warehouse

## 🎯 Core Capabilities

### Market Analysis & Scoring
- **4-Pillar Scoring**: Supply Constraints, Innovation Jobs, Urban Convenience, Outdoor Access
- **Risk Multipliers**: Climate, insurance, tax, and policy factors
- **Real-time Data**: Integration with Census, BLS, BEA, NOAA, and commercial sources

### Asset Evaluation & Fit Analysis
- **Product Type Matching**: Garden, mid-rise, mixed-use, adaptive reuse optimization
- **Guardrail Compliance**: Automated checks against investment criteria
- **Live Scoring**: Real-time fit calculations with market context

### Deal Structuring & ROI Analysis
- **Archetype Library**: Classic value-add, heavy repositioning, town-center infill
- **Scope Templates**: Light/medium/heavy renovation options with cost/benefit analysis
- **Payback Optimization**: ROI ranking and downtime minimization

### Portfolio Monitoring & Alerts
- **Exposure Analysis**: Multi-dimensional concentration monitoring
- **Threshold Alerts**: Automated breach detection and notification
- **Geographic Risk**: MSA and state-level concentration analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ with PostGIS extension

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd HousingModel
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Database setup
createdb aker_property_model
psql aker_property_model -c "CREATE EXTENSION postgis;"
alembic upgrade head
```

### Basic Usage

```python
from aker_core.config import Settings
from aker_portfolio import compute_exposures, PortfolioPosition

# Configure and analyze portfolio
settings = Settings()
positions = [PortfolioPosition(...)]
result = compute_exposures(positions, db_session=session)
```

## 📊 Key Metrics & Scoring

### Market Scoring (0-5 Scale)
- **Supply Constraints** (30%): Topography, regulatory friction, elasticity
- **Innovation Jobs** (30%): Tech/health/edu growth, human capital, migration
- **Urban Convenience** (20%): 15-minute access, retail health, transit
- **Outdoor Access** (20%): Recreation proximity, air quality, public lands

### Risk Multipliers (0.90-1.10)
- **Climate Risk**: Wildfire WUI, hail zones, snow load, water stress
- **Insurance Cost**: Premiums, deductibles, expected loss ratios
- **Tax Policy**: Reassessment cadence, appeals, special districts

## 🎨 User Interface

### Dashboard Pages
1. **Market Scorecard** - Interactive maps and pillar analysis
2. **Deal Workspace** - Archetype selection and ROI modeling
3. **Asset Fit Wizard** - Guided evaluation with live scoring
4. **Risk Panel** - Hazard mapping and insurance analysis
5. **Ops & Brand** - NPS tracking and reputation management
6. **Data Refresh** - Source management and lineage tracking
7. **Portfolio** - Exposure monitoring and alerts
8. **CO/UT/ID Patterning** - State-specific configurations

### Export Capabilities
- **Excel**: Multi-sheet workbooks with all analysis data
- **Word**: Formatted investment memos with charts
- **PDF**: Professional reports with data lineage

## 🔧 Configuration

### Environment Variables
```bash
# Database
AKER_DATABASE_URL=postgresql://user:pass@localhost/aker_property_model

# External APIs
AKER_CENSUS_API_KEY=your_census_key
AKER_BEA_API_KEY=your_bea_key

# Application
AKER_DEBUG=true
AKER_ALLOWED_ORIGINS=http://localhost:3000
```

## 🧪 Testing & Quality

### Quality Gates
```bash
# Run all quality checks
make quality  # Runs lint, type-check, test, coverage

# Individual checks
ruff check src tests --fix    # Linting
black .                       # Formatting
mypy src                      # Type checking
pytest --cov=src              # Test coverage
```

## 📈 Performance & Scalability

- **Market Scoring**: <5 minutes for state-scale analysis
- **Portfolio Analysis**: <2 seconds for 1000+ positions
- **API Response**: <500ms for standard operations
- **Dashboard Load**: <3 seconds for complex visualizations

## 🔒 Security & Compliance

- **Input Validation**: Comprehensive sanitization
- **Authentication**: Session-based with secure cookies
- **Audit Logging**: Complete activity tracking
- **PII Protection**: No personal data collection

## 🤝 Contributing

### Development Workflow
1. **Feature Branch**: `git checkout -b feature/new-capability`
2. **Test First**: Comprehensive test coverage required
3. **Code Review**: Required for all changes
4. **Documentation Gate**: Update knowledge base entries and run `scripts/enforce_documentation.py` before review

### Standards
- **Type Hints**: Required for all public APIs
- **Documentation**: Docstrings for public surfaces + knowledge base updates (see `docs/contributing/documentation.md`)
- **Testing**: 90%+ coverage for new features
- **Quality**: Ruff, Black, and mypy compliance required

## 📚 Documentation

### For Developers
- **API Reference**: Complete function documentation
- **Architecture Guide**: System design and patterns
- **Contributing Guide**: Development workflow

### For Users
- **Dashboard Manual**: Interface usage and navigation
- **Workflow Guides**: Step-by-step task completion
- **Data Dictionary**: Field definitions and business logic

### For Operators
- **Deployment Guide**: Installation and configuration
- **Monitoring Guide**: Health checks and troubleshooting
- **Backup Procedures**: Data protection and recovery

---

**Built with**: FastAPI, Dash, PostgreSQL, PostGIS, Prefect, and modern Python best practices

**License**: Proprietary - Contact Aker Property Model team for licensing

## 📚 Documentation

### For Developers
- **API Reference**: Complete documentation in module docstrings
- **Architecture Guide**: System design and patterns
- **Contributing Guide**: Development workflow and standards

### For Users
- **Dashboard Manual**: Interface usage and navigation
- **Workflow Guides**: Step-by-step task completion
- **Data Dictionary**: Field definitions and business logic

### For Operators
- **Deployment Guide**: Installation and configuration
- **Monitoring Guide**: Health checks and troubleshooting
- **Backup Procedures**: Data protection and recovery

## 🔍 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check database connectivity
python -c "from aker_data import Base; print('DB connection OK')"

# Verify environment variables
echo $AKER_DATABASE_URL
```

**Import Errors**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
pip list | grep aker
```

**Performance Issues**
```bash
# Check query performance
python -c "from aker_core.logging import get_logger; logger = get_logger('perf'); logger.info('Performance check')"

# Monitor memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

## 🤝 Contributing

### Development Workflow
1. **Feature Branch**: `git checkout -b feature/new-capability`
2. **Test First**: Comprehensive test coverage required
3. **Code Review**: Required for all changes
4. **Documentation Gate**: Update knowledge base entries and run `scripts/enforce_documentation.py` before review

### Standards
- **Type Hints**: Required for all public APIs
- **Documentation**: Docstrings for public surfaces + knowledge base updates (see `docs/contributing/documentation.md`)
- **Testing**: 90%+ coverage for new features
- **Quality**: Ruff, Black, and mypy compliance required

## 📞 Support

### Getting Help
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Comprehensive guides and references
- **Community**: Slack/Discord for real-time support

### Resources
- **API Documentation**: Auto-generated from code docstrings
- **Architecture Docs**: System design and patterns
- **Performance Guide**: Optimization and scaling
- **Security Guide**: Best practices and compliance

---

**Built with**: FastAPI, Dash, PostgreSQL, PostGIS, Prefect, and modern Python best practices

**License**: Proprietary - Contact Aker Property Model team for licensing information
