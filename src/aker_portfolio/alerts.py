from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .models import ExposureThresholds, PortfolioAlerts
from .types import ExposureThreshold, PortfolioAlert


class AlertManager:
    """Service for managing portfolio exposure alerts."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_threshold(
        self,
        dimension_type: str,
        threshold_pct: float,
        dimension_value: Optional[str] = None,
        threshold_type: str = "maximum",
        severity_level: str = "warning",
    ) -> ExposureThreshold:
        """Create a new exposure threshold."""
        from .models import ExposureThresholds

        threshold = ExposureThresholds(
            threshold_id=f"thresh_{dimension_type}_{dimension_value or 'global'}_{datetime.now().isoformat()}",
            dimension_type=dimension_type,
            dimension_value=dimension_value,
            threshold_pct=threshold_pct,
            threshold_type=threshold_type,
            severity_level=severity_level,
            is_active=True,
        )

        self.db_session.add(threshold)
        self.db_session.commit()

        return ExposureThreshold(
            threshold_id=threshold.threshold_id,
            dimension_type=threshold.dimension_type,
            dimension_value=threshold.dimension_value,
            threshold_pct=threshold.threshold_pct,
            threshold_type=threshold.threshold_type,
            severity_level=threshold.severity_level,
            is_active=threshold.is_active,
        )

    def update_threshold(
        self,
        threshold_id: str,
        threshold_pct: Optional[float] = None,
        severity_level: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> ExposureThreshold:
        """Update an existing threshold."""
        threshold = self.db_session.query(ExposureThresholds).filter(
            ExposureThresholds.threshold_id == threshold_id
        ).first()

        if not threshold:
            raise ValueError(f"Threshold {threshold_id} not found")

        if threshold_pct is not None:
            threshold.threshold_pct = threshold_pct
        if severity_level is not None:
            threshold.severity_level = severity_level
        if is_active is not None:
            threshold.is_active = is_active

        self.db_session.commit()

        return ExposureThreshold(
            threshold_id=threshold.threshold_id,
            dimension_type=threshold.dimension_type,
            dimension_value=threshold.dimension_value,
            threshold_pct=threshold.threshold_pct,
            threshold_type=threshold.threshold_type,
            severity_level=threshold.severity_level,
            is_active=threshold.is_active,
        )

    def get_thresholds(
        self, dimension_type: Optional[str] = None, active_only: bool = True
    ) -> list[ExposureThreshold]:
        """Get thresholds, optionally filtered."""
        query = self.db_session.query(ExposureThresholds)

        if dimension_type:
            query = query.filter(ExposureThresholds.dimension_type == dimension_type)
        if active_only:
            query = query.filter(ExposureThresholds.is_active.is_(True))

        thresholds = query.all()

        return [
            ExposureThreshold(
                threshold_id=thresh.threshold_id,
                dimension_type=thresh.dimension_type,
                dimension_value=thresh.dimension_value,
                threshold_pct=thresh.threshold_pct,
                threshold_type=thresh.threshold_type,
                severity_level=thresh.severity_level,
                is_active=thresh.is_active,
            )
            for thresh in thresholds
        ]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> PortfolioAlert:
        """Acknowledge an alert."""
        alert = self.db_session.query(PortfolioAlerts).filter(
            PortfolioAlerts.alert_id == alert_id
        ).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = "acknowledged"
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()

        self.db_session.commit()

        return PortfolioAlert(
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

    def resolve_alert(self, alert_id: str) -> PortfolioAlert:
        """Mark an alert as resolved."""
        alert = self.db_session.query(PortfolioAlerts).filter(
            PortfolioAlerts.alert_id == alert_id
        ).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = "resolved"
        alert.resolved_at = datetime.now()

        self.db_session.commit()

        return PortfolioAlert(
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

    def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> list[PortfolioAlert]:
        """Get alerts with optional filtering."""
        query = self.db_session.query(PortfolioAlerts)

        if status:
            query = query.filter(PortfolioAlerts.status == status)
        if severity:
            query = query.filter(PortfolioAlerts.severity == severity)

        alerts = query.order_by(PortfolioAlerts.created_at.desc()).limit(limit).all()

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

    def get_alert_summary(self) -> dict:
        """Get summary of alert status."""
        total_alerts = self.db_session.query(PortfolioAlerts).count()

        status_counts = {}
        for status in ["active", "acknowledged", "resolved"]:
            count = self.db_session.query(PortfolioAlerts).filter(
                PortfolioAlerts.status == status
            ).count()
            status_counts[status] = count

        severity_counts = {}
        for severity in ["warning", "critical"]:
            count = self.db_session.query(PortfolioAlerts).filter(
                PortfolioAlerts.severity == severity
            ).count()
            severity_counts[severity] = count

        return {
            "total_alerts": total_alerts,
            "status_breakdown": status_counts,
            "severity_breakdown": severity_counts,
            "active_alerts": status_counts.get("active", 0),
            "unacknowledged_alerts": status_counts.get("active", 0),
        }
