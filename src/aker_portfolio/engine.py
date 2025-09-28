from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from aker_core.run import RunContext

from .models import ExposureThresholds, PortfolioAlerts, PortfolioExposures
from .types import (
    ExposureDimension,
    ExposureRequest,
    ExposureResult,
    PortfolioAlert,
    PortfolioPosition,
)


class PortfolioEngine:
    """Core portfolio exposure computation and alert engine."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def compute_exposures(self, request: ExposureRequest) -> ExposureResult:
        """
        Compute portfolio exposures across multiple dimensions.

        Args:
            request: Exposure calculation request with positions and parameters

        Returns:
            ExposureResult with calculated exposures and alerts
        """
        as_of_date = request.as_of_date or datetime.now()
        positions = request.positions

        # Calculate total portfolio value
        total_value = sum(pos.position_value for pos in positions)

        if total_value == 0:
            raise ValueError("Total portfolio value cannot be zero")

        # Group positions by dimensions and calculate exposures
        exposures = self._calculate_dimension_exposures(positions, total_value)

        # Create exposure result
        result = ExposureResult(
            as_of_date=as_of_date,
            total_portfolio_value=total_value,
            exposures=exposures,
        )

        # Persist exposures
        self._persist_exposures(result)

        # Check thresholds and generate alerts if requested
        if request.include_alerts:
            self._check_thresholds_and_generate_alerts(result)
            # TODO: Store alerts in result metadata

        return result

    def _calculate_dimension_exposures(
        self, positions: list[PortfolioPosition], total_value: float
    ) -> list[ExposureDimension]:
        """Calculate exposures for all relevant dimensions."""
        exposures = []

        # Define dimensions to calculate
        dimensions = [
            ("strategy", lambda p: p.strategy),
            ("state", lambda p: p.state),
            ("msa", lambda p: p.msa_id),
            ("vintage", lambda p: str(p.vintage) if p.vintage else None),
            ("construction_type", lambda p: p.construction_type),
            ("rent_band", lambda p: p.rent_band),
        ]

        for dim_type, value_func in dimensions:
            dim_exposures = self._calculate_single_dimension_exposure(
                positions, total_value, dim_type, value_func
            )
            exposures.extend(dim_exposures)

        return exposures

    def _calculate_single_dimension_exposure(
        self,
        positions: list[PortfolioPosition],
        total_value: float,
        dimension_type: str,
        value_func,
    ) -> list[ExposureDimension]:
        """Calculate exposure for a single dimension."""
        # Group positions by dimension value
        dimension_groups = defaultdict(list)
        for position in positions:
            value = value_func(position)
            if value is not None:
                dimension_groups[value].append(position)

        # Calculate exposure for each group
        exposures = []
        for dim_value, pos_list in dimension_groups.items():
            group_value = sum(pos.position_value for pos in pos_list)
            exposure_pct = (group_value / total_value) * 100

            exposure = ExposureDimension(
                dimension_type=dimension_type,
                dimension_value=dim_value,
                exposure_pct=exposure_pct,
                exposure_value=group_value,
                total_portfolio_value=total_value,
            )
            exposures.append(exposure)

        return exposures

    def _persist_exposures(self, result: ExposureResult) -> None:
        """Persist exposure calculations to database."""
        run_id = None
        try:
            # Try to get run_id from context
            run_context = RunContext.get_current()
            run_id = run_context.run_id if run_context else None
        except Exception:
            # Fallback if no run context
            pass

        for exposure in result.exposures:
            db_exposure = PortfolioExposures(
                exposure_id=str(uuid.uuid4()),
                dimension_type=exposure.dimension_type,
                dimension_value=exposure.dimension_value,
                exposure_pct=exposure.exposure_pct,
                exposure_value=exposure.exposure_value,
                total_portfolio_value=exposure.total_portfolio_value,
                as_of_date=result.as_of_date,
                run_id=run_id,
            )
            self.db_session.add(db_exposure)

        self.db_session.commit()

    def _check_thresholds_and_generate_alerts(
        self, result: ExposureResult
    ) -> list[PortfolioAlert]:
        """Check exposure thresholds and generate alerts."""
        alerts = []

        # Get active thresholds
        thresholds = (
            self.db_session
            .query(ExposureThresholds)
            .filter(ExposureThresholds.is_active.is_(True))
            .all()
        )

        for exposure in result.exposures:
            for threshold in thresholds:
                # Check if threshold applies to this dimension
                if (threshold.dimension_type == exposure.dimension_type and
                    (threshold.dimension_value is None or
                     threshold.dimension_value == exposure.dimension_value)):

                    # Check if breach occurred
                    breach_detected = False
                    if threshold.threshold_type == "maximum" and exposure.exposure_pct > threshold.threshold_pct:
                        breach_detected = True
                    elif threshold.threshold_type == "minimum" and exposure.exposure_pct < threshold.threshold_pct:
                        breach_detected = True

                    if breach_detected:
                        alert = self._create_alert(threshold, exposure, result)
                        alerts.append(alert)

        # Persist alerts
        for alert in alerts:
            db_alert = PortfolioAlerts(
                alert_id=str(uuid.uuid4()),
                threshold_id=alert.threshold_id,
                exposure_id=alert.exposure_id,
                breach_pct=alert.breach_pct,
                alert_message=alert.alert_message,
                severity=alert.severity,
                status=alert.status,
            )
            self.db_session.add(db_alert)

        if alerts:
            self.db_session.commit()

        return alerts

    def _create_alert(
        self, threshold: ExposureThresholds, exposure: ExposureDimension, result: ExposureResult
    ) -> PortfolioAlert:
        """Create alert for threshold breach."""
        breach_pct = abs(exposure.exposure_pct - threshold.threshold_pct)

        if threshold.threshold_type == "maximum":
            message = (
                f"Exposure threshold breached: {exposure.dimension_type}='{exposure.dimension_value}' "
                f"at {exposure.exposure_pct:.1f}% exceeds maximum of {threshold.threshold_pct:.1f}%"
            )
        else:
            message = (
                f"Exposure threshold breached: {exposure.dimension_type}='{exposure.dimension_value}' "
                f"at {exposure.exposure_pct:.1f}% below minimum of {threshold.threshold_pct:.1f}%"
            )

        return PortfolioAlert(
            threshold_id=threshold.threshold_id,
            exposure_id=f"{exposure.dimension_type}_{exposure.dimension_value}_{result.as_of_date.isoformat()}",
            breach_pct=breach_pct,
            alert_message=message,
            severity=threshold.severity_level,
            status="active",
        )

    def get_exposures_by_date(
        self, as_of_date: datetime, dimension_type: Optional[str] = None
    ) -> list[ExposureDimension]:
        """Retrieve exposure calculations for a specific date."""
        query = self.db_session.query(PortfolioExposures).filter(
            PortfolioExposures.as_of_date == as_of_date
        )

        if dimension_type:
            query = query.filter(PortfolioExposures.dimension_type == dimension_type)

        exposures = query.all()

        return [
            ExposureDimension(
                dimension_type=exp.dimension_type,
                dimension_value=exp.dimension_value,
                exposure_pct=exp.exposure_pct,
                exposure_value=exp.exposure_value,
                total_portfolio_value=exp.total_portfolio_value,
            )
            for exp in exposures
        ]

    def get_active_alerts(self) -> list[PortfolioAlert]:
        """Retrieve all active alerts."""
        alerts = self.db_session.query(PortfolioAlerts).filter(
            PortfolioAlerts.status == "active"
        ).all()

        return [
            PortfolioAlert(
                alert_id=alert.alert_id,
                threshold_id=alert.threshold_id,
                exposure_id=alert.exposure_id,
                breach_pct=alert.breach_pct,
                alert_message=alert.alert_message,
                severity=alert.severity,
                status=alert.status,
                acknowledged_by=alert.acknowledged_by,
                acknowledged_at=alert.acknowledged_at,
                resolved_at=alert.resolved_at,
                created_at=alert.created_at,
            )
            for alert in alerts
        ]
