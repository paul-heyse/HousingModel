"""
Tests for Aker Core Market Pillar Scoring

Tests the pillar aggregation and scoring functionality for the Aker Property Model.
"""

import math
from datetime import date, datetime
from unittest.mock import Mock

import pytest

from aker_core.markets.composer import MarketPillarScores, _normalise_weights, score


class TestMarketPillarScores:
    """Test cases for MarketPillarScores dataclass."""

    def test_market_pillar_scores_creation(self):
        """Test basic MarketPillarScores creation."""
        scores = MarketPillarScores(
            msa_id="MSA001",
            supply_0_5=3.5,
            jobs_0_5=4.0,
            urban_0_5=3.8,
            outdoor_0_5=3.2,
            weighted_0_5=3.7,
            weighted_0_100=74.0,
            weights={"supply": 0.3, "jobs": 0.3, "urban": 0.2, "outdoor": 0.2},
            score_as_of=date(2023, 9, 15),
            run_id=12345
        )

        assert scores.msa_id == "MSA001"
        assert scores.supply_0_5 == 3.5
        assert scores.jobs_0_5 == 4.0
        assert scores.urban_0_5 == 3.8
        assert scores.outdoor_0_5 == 3.2
        assert scores.weighted_0_5 == 3.7
        assert scores.weighted_0_100 == 74.0
        assert scores.score_as_of == date(2023, 9, 15)
        assert scores.run_id == 12345

    def test_to_dict_export(self):
        """Test dictionary export functionality."""
        scores = MarketPillarScores(
            msa_id="MSA001",
            supply_0_5=3.5,
            jobs_0_5=4.0,
            urban_0_5=3.8,
            outdoor_0_5=3.2,
            weighted_0_5=3.7,
            weighted_0_100=74.0,
            weights={"supply": 0.3, "jobs": 0.3, "urban": 0.2, "outdoor": 0.2},
            score_as_of=date(2023, 9, 15),
            run_id=12345
        )

        result = scores.to_dict()

        assert result["msa_id"] == "MSA001"
        assert result["supply_0_5"] == 3.5
        assert result["weighted_0_100"] == 74.0
        assert result["weight_supply"] == 0.3
        assert result["weight_jobs"] == 0.3
        assert result["score_as_of"] == "2023-09-15"
        assert result["run_id"] == 12345


class TestScoreFunction:
    """Test cases for the score function."""

    def test_default_weight_composition(self):
        """Test score calculation with default Aker weights."""
        # Mock database record
        mock_record = Mock()
        mock_record.supply_0_5 = 3.5
        mock_record.jobs_0_5 = 4.0
        mock_record.urban_0_5 = 3.8
        mock_record.outdoor_0_5 = 3.2

        # Mock session and query
        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        result = score(session=mock_session, msa_id="MSA001")

        # Verify calculation: 0.3*3.5 + 0.3*4.0 + 0.2*3.8 + 0.2*3.2 = 3.65
        assert math.isclose(result.weighted_0_5, 3.65)
        assert math.isclose(result.weighted_0_100, 73.0)

    def test_custom_weight_composition(self):
        """Test score calculation with custom weights."""
        mock_record = Mock()
        mock_record.supply_0_5 = 3.5
        mock_record.jobs_0_5 = 4.0
        mock_record.urban_0_5 = 3.8
        mock_record.outdoor_0_5 = 3.2

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        # Custom weights: 0.4, 0.4, 0.1, 0.1
        custom_weights = {"supply": 0.4, "jobs": 0.4, "urban": 0.1, "outdoor": 0.1}
        result = score(session=mock_session, msa_id="MSA001", weights=custom_weights)

        # Verify calculation: 0.4*3.5 + 0.4*4.0 + 0.1*3.8 + 0.1*3.2 = 3.7
        assert math.isclose(result.weighted_0_5, 3.7)
        assert math.isclose(result.weighted_0_100, 74.0)

    def test_missing_pillar_data(self):
        """Test error handling for missing pillar data."""
        mock_record = Mock()
        mock_record.supply_0_5 = 3.5
        mock_record.jobs_0_5 = None  # Missing jobs score
        mock_record.urban_0_5 = 3.8
        mock_record.outdoor_0_5 = 3.2

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        with pytest.raises(ValueError, match="Missing pillar scores"):
            score(session=mock_session, msa_id="MSA001")

    def test_no_pillar_data(self):
        """Test error handling when no pillar data exists."""
        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = None

        with pytest.raises(ValueError, match="No pillar scores available"):
            score(session=mock_session, msa_id="MSA001")

    def test_database_persistence(self):
        """Test that scores are persisted to database."""
        mock_record = Mock()
        mock_record.supply_0_5 = 3.5
        mock_record.jobs_0_5 = 4.0
        mock_record.urban_0_5 = 3.8
        mock_record.outdoor_0_5 = 3.2
        mock_record.weighted_0_5 = None  # Will be set by function
        mock_record.weighted_0_100 = None
        mock_record.weights = None
        mock_record.score_as_of = None
        mock_record.run_id = None

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record
        mock_session.flush = Mock()

        score(session=mock_session, msa_id="MSA001")

        # Verify database updates
        assert math.isclose(mock_record.weighted_0_5, 3.65)
        assert math.isclose(mock_record.weighted_0_100, 73.0)
        assert mock_record.weights == {"supply": 0.3, "jobs": 0.3, "urban": 0.2, "outdoor": 0.2}
        mock_session.flush.assert_called_once()


class TestWeightNormalization:
    """Test cases for weight normalization functionality."""

    def test_weight_normalization(self):
        """Test that weights are properly normalized."""
        weights = {"supply": 0.4, "jobs": 0.4, "urban": 0.1, "outdoor": 0.1}
        normalized = _normalise_weights(weights)

        assert sum(normalized.values()) == pytest.approx(1.0, abs=1e-10)
        assert normalized["supply"] == 0.4
        assert normalized["jobs"] == 0.4
        assert normalized["urban"] == 0.1
        assert normalized["outdoor"] == 0.1

    def test_default_weights(self):
        """Test that default weights are returned when no overrides provided."""
        normalized = _normalise_weights(None)

        assert sum(normalized.values()) == 1.0
        assert normalized["supply"] == 0.3
        assert normalized["jobs"] == 0.3
        assert normalized["urban"] == 0.2
        assert normalized["outdoor"] == 0.2

    def test_negative_weights_error(self):
        """Test error handling for negative weights."""
        weights = {"supply": -0.1, "jobs": 0.3, "urban": 0.4, "outdoor": 0.4}

        with pytest.raises(ValueError, match="Pillar weights must be non-negative"):
            _normalise_weights(weights)

    def test_zero_total_weights_error(self):
        """Test error handling for zero total weights."""
        weights = {"supply": 0.0, "jobs": 0.0, "urban": 0.0, "outdoor": 0.0}

        with pytest.raises(ValueError, match="At least one pillar weight must be greater than zero"):
            _normalise_weights(weights)

    def test_partial_weights_normalization(self):
        """Test normalization with partial weight specification."""
        weights = {"supply": 0.6, "jobs": 0.4}  # Missing urban and outdoor
        normalized = _normalise_weights(weights)

        # Should fill missing with 0 and normalize
        assert normalized["supply"] == 0.6
        assert normalized["jobs"] == 0.4
        assert normalized["urban"] == 0.0
        assert normalized["outdoor"] == 0.0


class TestDateHandling:
    """Test cases for date handling functionality."""

    def test_date_parsing_iso_string(self):
        """Test parsing of ISO date strings."""
        from aker_core.markets.composer import _as_date

        result = _as_date("2023-09-15")
        assert result == date(2023, 9, 15)

    def test_date_parsing_datetime_object(self):
        """Test parsing of datetime objects."""
        from aker_core.markets.composer import _as_date

        dt = datetime(2023, 9, 15, 14, 30, 45)
        result = _as_date(dt)
        assert result == date(2023, 9, 15)

    def test_date_parsing_date_object(self):
        """Test parsing of date objects."""
        from aker_core.markets.composer import _as_date

        d = date(2023, 9, 15)
        result = _as_date(d)
        assert result == d

    def test_date_parsing_none(self):
        """Test handling of None values."""
        from aker_core.markets.composer import _as_date

        result = _as_date(None)
        assert result is None

    def test_date_parsing_year_month_string(self):
        """Test parsing of YYYY-MM strings."""
        from aker_core.markets.composer import _as_date

        result = _as_date("2023-09")
        assert result == date(2023, 9, 1)

    def test_date_parsing_invalid_string(self):
        """Test error handling for invalid date strings."""
        from aker_core.markets.composer import _as_date

        with pytest.raises(TypeError, match="score_as_of must be a date"):
            _as_date("invalid-date")


class TestMathematicalProperties:
    """Test mathematical properties of the scoring system."""

    def test_weighted_average_property(self):
        """Test that weighted average is correctly calculated."""
        # Test case: equal weights should give simple average
        mock_record = Mock()
        mock_record.supply_0_5 = 3.0
        mock_record.jobs_0_5 = 3.0
        mock_record.urban_0_5 = 3.0
        mock_record.outdoor_0_5 = 3.0

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        result = score(session=mock_session, msa_id="MSA001")

        # With equal weights, should be simple average
        assert result.weighted_0_5 == 3.0
        assert result.weighted_0_100 == 60.0

    def test_zero_weights_handling(self):
        """Test handling of zero weights."""
        mock_record = Mock()
        mock_record.supply_0_5 = 3.0
        mock_record.jobs_0_5 = 4.0
        mock_record.urban_0_5 = 3.5
        mock_record.outdoor_0_5 = 3.2

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        # Weights with zero for urban and outdoor
        weights = {"supply": 0.5, "jobs": 0.5, "urban": 0.0, "outdoor": 0.0}
        result = score(session=mock_session, msa_id="MSA001", weights=weights)

        # Should only use supply and jobs: 0.5*3.0 + 0.5*4.0 = 3.5
        assert result.weighted_0_5 == 3.5
        assert result.weighted_0_100 == 70.0

    def test_score_bounds(self):
        """Test that scores stay within expected bounds."""
        # Test with extreme values
        mock_record = Mock()
        mock_record.supply_0_5 = 0.0
        mock_record.jobs_0_5 = 5.0
        mock_record.urban_0_5 = 0.0
        mock_record.outdoor_0_5 = 5.0

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        result = score(session=mock_session, msa_id="MSA001")

        # Should be bounded: 0.3*0 + 0.3*5 + 0.2*0 + 0.2*5 = 2.5
        assert 0 <= result.weighted_0_5 <= 5.0
        assert result.weighted_0_5 == 2.5

    def test_deterministic_output(self):
        """Test that identical inputs produce identical outputs."""
        mock_record = Mock()
        mock_record.supply_0_5 = 3.5
        mock_record.jobs_0_5 = 4.0
        mock_record.urban_0_5 = 3.8
        mock_record.outdoor_0_5 = 3.2

        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

        result1 = score(session=mock_session, msa_id="MSA001")
        result2 = score(session=mock_session, msa_id="MSA001")

        assert result1.weighted_0_5 == result2.weighted_0_5
        assert result1.weighted_0_100 == result2.weighted_0_100
        assert result1.weights == result2.weights


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_session(self):
        """Test error handling for invalid session."""
        with pytest.raises(ValueError, match="An active SQLAlchemy session is required"):
            score(session=None, msa_id="MSA001")

    def test_missing_msa_id(self):
        """Test error handling for missing MSA ID."""
        mock_session = Mock()

        with pytest.raises(ValueError, match="msa_id is required"):
            score(session=mock_session, msa_id=None)

    def test_msa_geo_without_msa_id(self):
        """Test error handling for msa_geo without msa_id."""
        mock_session = Mock()

        with pytest.raises(ValueError, match="msa_geo lookups require a resolved msa_id"):
            score(session=mock_session, msa_id=None, msa_geo="POINT(-122.4 37.8)")


class TestIntegration:
    """Integration tests for pillar scoring."""

    def test_end_to_end_scoring_workflow(self):
        """Test complete scoring workflow from raw data to final scores."""
        # This would test the complete integration
        # For now, just verify the function exists and can be called
        from aker_core.markets import score

        assert callable(score)

    def test_score_with_real_database(self):
        """Test scoring with actual database session (placeholder)."""
        # This would require a real database connection
        # For now, just verify the interface
        pass
