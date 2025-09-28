"""Tests for portfolio exposure monitoring functionality."""


from datetime import datetime

from aker_portfolio import PortfolioPosition, compute_exposures
from aker_portfolio.engine import PortfolioEngine


class TestPortfolioExposure:
    """Test portfolio exposure calculations."""

    def test_compute_exposures_basic(self, db_session):
        """Test basic exposure calculation."""
        positions = [
            PortfolioPosition(
                asset_id="asset_1",
                strategy="value_add",
                state="CA",
                msa_id="31080",  # Los Angeles
                position_value=1000000,
                units=50,
            ),
            PortfolioPosition(
                asset_id="asset_2",
                strategy="value_add",
                state="TX",
                msa_id="19100",  # Dallas
                position_value=1500000,
                units=75,
            ),
            PortfolioPosition(
                asset_id="asset_3",
                strategy="core_plus",
                state="CA",
                msa_id="41860",  # San Francisco
                position_value=2000000,
                units=100,
            ),
        ]

        result = compute_exposures(positions, db_session=db_session)

        # Check total portfolio value
        assert result.total_portfolio_value == 4500000

        # Check strategy exposures
        strategy_exposures = {
            exp.dimension_value: exp.exposure_pct
            for exp in result.exposures
            if exp.dimension_type == "strategy"
        }

        assert "value_add" in strategy_exposures
        assert "core_plus" in strategy_exposures
        assert abs(strategy_exposures["value_add"] - (2500000 / 4500000 * 100)) < 0.01
        assert abs(strategy_exposures["core_plus"] - (2000000 / 4500000 * 100)) < 0.01

        # Check state exposures
        state_exposures = {
            exp.dimension_value: exp.exposure_pct
            for exp in result.exposures
            if exp.dimension_type == "state"
        }

        assert "CA" in state_exposures
        assert "TX" in state_exposures
        assert abs(state_exposures["CA"] - (3000000 / 4500000 * 100)) < 0.01
        assert abs(state_exposures["TX"] - (1500000 / 4500000 * 100)) < 0.01

    def test_compute_exposures_with_alerts(self, db_session):
        """Test exposure calculation with alert generation."""
        # First create a threshold that will be breached
        from aker_portfolio.alerts import AlertManager

        alert_manager = AlertManager(db_session)
        alert_manager.create_threshold(
            dimension_type="strategy",
            dimension_value="value_add",
            threshold_pct=30.0,  # 30% threshold
            severity_level="critical",
        )

        positions = [
            PortfolioPosition(
                asset_id="asset_1",
                strategy="value_add",
                position_value=400000,  # 40% of total
                units=20,
            ),
            PortfolioPosition(
                asset_id="asset_2",
                strategy="core_plus",
                position_value=600000,  # 60% of total
                units=30,
            ),
        ]

        compute_exposures(positions, include_alerts=True, db_session=db_session)

        # Check that alert was generated
        engine = PortfolioEngine(db_session)
        alerts = engine.get_active_alerts()

        # Should have one critical alert for value_add exceeding 30%
        assert len(alerts) == 1
        assert alerts[0].severity == "critical"
        assert "value_add" in alerts[0].alert_message
        assert alerts[0].breach_pct > 0  # Should have calculated breach percentage

    def test_position_normalization(self):
        """Test position normalization functionality."""
        from aker_portfolio.normalization import PortfolioPositionNormalizer

        positions = [
            PortfolioPosition(
                strategy="VALUE_ADD",  # Mixed case
                state="ca",  # Lowercase
                construction_type=" New Construction ",  # Extra spaces
                position_value=1000000,
                units=50,
            ),
            PortfolioPosition(
                position_value=0,  # Invalid value
                units=50,
            ),
        ]

        normalizer = PortfolioPositionNormalizer()
        normalized = normalizer.normalize_position_values(positions)

        # Should have normalized the valid position
        assert len(normalized) == 1
        assert normalized[0].strategy == "value_add"
        assert normalized[0].state == "CA"
        assert normalized[0].construction_type == "new construction"

        # Should have filtered out invalid position
        validation = normalizer.validate_positions(normalized)
        assert validation.is_valid

    def test_threshold_management(self, db_session):
        """Test threshold creation and management."""
        from aker_portfolio.alerts import AlertManager

        alert_manager = AlertManager(db_session)

        # Create a threshold
        threshold = alert_manager.create_threshold(
            dimension_type="state",
            dimension_value="CA",
            threshold_pct=25.0,
            threshold_type="maximum",
            severity_level="warning",
        )

        assert threshold.dimension_type == "state"
        assert threshold.dimension_value == "CA"
        assert threshold.threshold_pct == 25.0
        assert threshold.severity_level == "warning"

        # Get thresholds
        thresholds = alert_manager.get_thresholds(dimension_type="state")
        assert len(thresholds) == 1
        assert thresholds[0].dimension_value == "CA"

        # Update threshold
        updated = alert_manager.update_threshold(
            threshold_id=threshold.threshold_id,
            threshold_pct=30.0,
            severity_level="critical",
        )

        assert updated.threshold_pct == 30.0
        assert updated.severity_level == "critical"

    def test_geographic_analysis(self, db_session):
        """Test geographic concentration analysis."""
        from aker_portfolio.geographic import GeographicExposureAnalyzer

        analyzer = GeographicExposureAnalyzer(db_session)

        # Create some test exposures
        exposures = [
            {"dimension_type": "msa", "dimension_value": "31080", "exposure_pct": 35.0, "exposure_value": 1000000},
            {"dimension_type": "msa", "dimension_value": "19100", "exposure_pct": 25.0, "exposure_value": 750000},
            {"dimension_type": "msa", "dimension_value": "41860", "exposure_pct": 20.0, "exposure_value": 600000},
            {"dimension_type": "msa", "dimension_value": "37980", "exposure_pct": 15.0, "exposure_value": 450000},
            {"dimension_type": "msa", "dimension_value": "45300", "exposure_pct": 5.0, "exposure_value": 150000},
        ]

        # This would normally come from the engine, but for testing we'll simulate
        from aker_portfolio.types import ExposureDimension
        exp_objects = [
            ExposureDimension(
                dimension_type=exp["dimension_type"],
                dimension_value=exp["dimension_value"],
                exposure_pct=exp["exposure_pct"],
                exposure_value=exp["exposure_value"],
                total_portfolio_value=3000000,
            )
            for exp in exposures
        ]

        msa_exposures = [exp for exp in exp_objects if exp.dimension_type == "msa"]
        analysis = analyzer._analyze_msa_concentrations(msa_exposures)

        assert analysis["top_1_exposure_pct"] == 35.0
        assert analysis["top_3_exposure_pct"] == 80.0  # 35 + 25 + 20
        assert analysis["num_msas"] == 5
        assert len(analysis["msa_details"]) == 5

    def test_visualization_components(self):
        """Test dashboard visualization components."""
        from datetime import datetime

        # Create test exposure result
        from aker_portfolio.types import ExposureDimension, ExposureResult
        from aker_portfolio.visualization import ExposureVisualization

        exposures = [
            ExposureDimension("strategy", "value_add", 40.0, 1000000, 2500000),
            ExposureDimension("strategy", "core_plus", 60.0, 1500000, 2500000),
            ExposureDimension("state", "CA", 40.0, 1000000, 2500000),
            ExposureDimension("state", "TX", 60.0, 1500000, 2500000),
        ]

        result = ExposureResult(
            as_of_date=datetime.now(),
            total_portfolio_value=2500000,
            exposures=exposures,
        )

        # Test visualization
        viz = ExposureVisualization(result)
        dial_data = viz.get_exposure_dials_data()

        assert len(dial_data) == 2  # Strategy and geographic dials
        assert dial_data[0]["type"] == "strategy"
        assert dial_data[1]["type"] == "geographic"

        # Test chart data
        chart_data = viz.get_exposure_chart_data()
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert len(chart_data["datasets"][0]["data"]) == 6  # 6 dimension types

    def test_import_export_functionality(self):
        """Test import/export utilities."""
        from aker_portfolio.import_export import PortfolioExporter, PortfolioPositionImporter
        from aker_portfolio.types import PortfolioPosition

        # Create test positions
        positions = [
            PortfolioPosition(
                position_id="pos_1",
                asset_id="asset_1",
                strategy="value_add",
                state="CA",
                position_value=1000000,
            ),
            PortfolioPosition(
                position_id="pos_2",
                asset_id="asset_2",
                strategy="core_plus",
                state="TX",
                position_value=1500000,
            ),
        ]

        # Test CSV export
        csv_data = PortfolioExporter.exposures_to_csv([])
        assert "dimension_type,dimension_value" in csv_data

        # Test JSON export
        from aker_portfolio.types import ExposureResult
        result = ExposureResult(
            as_of_date=datetime.now(),
            total_portfolio_value=2500000,
            exposures=positions[:1],  # Use one position as exposure
        )
        json_data = PortfolioExporter.exposures_to_json(result)
        assert "total_portfolio_value" in json_data
        assert "exposures" in json_data

        # Test CSV import
        csv_import = """position_id,asset_id,strategy,state,position_value
pos_1,asset_1,value_add,CA,1000000
pos_2,asset_2,core_plus,TX,1500000"""

        imported_positions = PortfolioPositionImporter.from_csv(csv_import)
        assert len(imported_positions) == 2
        assert imported_positions[0].strategy == "value_add"
        assert imported_positions[1].strategy == "core_plus"

    def test_performance_benchmarking(self):
        """Test performance benchmarking utilities."""
        from aker_portfolio.performance import PerformanceBenchmark

        # Create test positions
        positions = [
            PortfolioPosition(
                position_id=f"pos_{i}",
                strategy="value_add",
                state="CA",
                position_value=100000,
            ) for i in range(10)
        ]

        # Test benchmarking
        benchmark = PerformanceBenchmark()
        result = benchmark.benchmark_exposure_calculation(positions, num_runs=2)

        assert result["success"]
        assert result["num_positions"] == 10
        assert "avg_time" in result
        assert "positions_per_second" in result

        # Test scalability
        scalability = benchmark.benchmark_scalability(positions[:2], [1, 2])
        assert "2_positions" in scalability
        assert "4_positions" in scalability

    def test_alert_management(self, db_session):
        """Test alert management functionality."""
        from aker_portfolio.alerts import AlertManager

        alert_manager = AlertManager(db_session)

        # Test threshold creation
        threshold = alert_manager.create_threshold(
            dimension_type="strategy",
            dimension_value="value_add",
            threshold_pct=30.0,
            severity_level="warning",
        )

        assert threshold.dimension_type == "strategy"
        assert threshold.threshold_pct == 30.0

        # Test threshold retrieval
        thresholds = alert_manager.get_thresholds(dimension_type="strategy")
        assert len(thresholds) >= 1

        # Test threshold update
        updated = alert_manager.update_threshold(
            threshold_id=threshold.threshold_id,
            threshold_pct=35.0,
            severity_level="critical",
        )

        assert updated.threshold_pct == 35.0
        assert updated.severity_level == "critical"
