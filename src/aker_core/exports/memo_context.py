"""Memo context assembly and sanitisation utilities."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from sqlalchemy.orm import Session

LOGGER = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}")


@dataclass(frozen=True)
class MemoContextPayload:
    """Structured payload returned by :class:`MemoContextBuilder`."""

    data: Dict[str, Any]
    metadata: Dict[str, Any]


class MemoContextBuilder:
    """Assemble memo-ready context dictionaries from domain inputs.

    The builder does light validation, applies defaults for optional sections,
    and removes obvious PII artefacts from review narratives so that exported
    memos are compliant with internal policies.
    """

    def __init__(self, session: Optional[Session] = None, logger: Optional[logging.Logger] = None) -> None:
        self.session = session
        self.logger = logger or LOGGER

    def build(
        self,
        *,
        msa: Mapping[str, Any],
        market_tables: Mapping[str, Iterable[Mapping[str, Any]]],
        risk: Mapping[str, Any],
        data_vintage: Mapping[str, str],
        run_id: str,
        git_sha: str,
        created_at: datetime,
        images: Mapping[str, str | Path],
        asset: Optional[Mapping[str, Any]] = None,
        ops: Optional[Mapping[str, Any]] = None,
        state_pack: Optional[Mapping[str, Any]] = None,
    ) -> MemoContextPayload:
        """Construct the memo context and metadata.

        Args:
            msa: Base market information (name, as_of, pillar scores, etc.).
            market_tables: Dict with table collections for supply/jobs/urban/outdoors.
            risk: Risk context including multipliers and summary deltas.
            data_vintage: Mapping of data source to vintage string (YYYY-MM).
            run_id: Run identifier associated with the export.
            git_sha: Git commit hash for reproducibility metadata.
            created_at: Timestamp for memo footer.
            images: Mapping of image keys to file paths.
            asset: Optional asset fit information.
            ops: Optional operations metrics (reputation, NPS, reviews).
            state_pack: Optional state policy adjustments payload.

        Returns:
            :class:`MemoContextPayload` containing memo context ready for templating
            and metadata describing redactions performed during sanitisation.
        """
        context: MutableMapping[str, Any] = {}
        metadata: Dict[str, Any] = {}

        context["msa"] = self._build_msa(msa, run_id=run_id, git_sha=git_sha)
        context["market_tables"] = self._normalise_tables(market_tables)
        context["risk"] = self._normalise_risk(risk)
        context["data_vintage"] = dict(data_vintage)
        context["run_id"] = run_id
        context["git_sha"] = git_sha
        context["created_at"] = created_at.isoformat()

        context["asset"] = self._normalise_asset(asset)
        ops_payload, redactions = self._normalise_ops(ops)
        context["ops"] = ops_payload
        metadata["redactions"] = redactions

        context["state_pack"] = self._normalise_state_pack(state_pack)
        context["images"] = {key: str(Path(value)) for key, value in images.items()}

        return MemoContextPayload(data=dict(context), metadata=metadata)

    def _build_msa(self, msa: Mapping[str, Any], *, run_id: str, git_sha: str) -> Dict[str, Any]:
        if "name" not in msa or "as_of" not in msa:
            raise ValueError("msa mapping must include 'name' and 'as_of' keys")

        pillar_scores = dict(msa.get("pillar_scores", {}))
        required_scores = {"weighted_0_5", "risk_multiplier"}
        missing = required_scores - pillar_scores.keys()
        if missing:
            raise ValueError(f"msa.pillar_scores missing keys: {sorted(missing)}")

        payload = dict(msa)
        payload.setdefault("run_id", run_id)
        payload.setdefault("git_sha", git_sha)
        payload["pillar_scores"] = pillar_scores
        return payload

    def _normalise_tables(
        self,
        tables: Mapping[str, Iterable[Mapping[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        expected_sections = ("supply", "jobs", "urban", "outdoors")
        normalised: Dict[str, List[Dict[str, Any]]] = {}
        for section in expected_sections:
            rows = tables.get(section, [])
            normalised[section] = [dict(row) for row in rows]
        return normalised

    def _normalise_risk(self, risk: Mapping[str, Any]) -> Dict[str, Any]:
        multipliers = risk.get("multipliers")
        if multipliers is None:
            raise ValueError("risk context must include 'multipliers'")
        return {
            "multipliers": [dict(row) for row in multipliers],
            "exit_cap_bps_delta": risk.get("exit_cap_bps_delta", 0),
            "contingency_pct_delta": risk.get("contingency_pct_delta", 0),
        }

    def _normalise_asset(self, asset: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if not asset:
            return {
                "fit_score": "No asset context provided",
                "flags": [
                    {
                        "severity": "info",
                        "code": "—",
                        "message": "No asset context provided",
                        "observed": "—",
                        "target": "—",
                    }
                ],
            }

        payload = dict(asset)
        payload.setdefault("flags", [])
        return payload

    def _normalise_ops(self, ops: Optional[Mapping[str, Any]]) -> tuple[Dict[str, Any], int]:
        redactions = 0
        if not ops:
            return (
                {
                    "reputation_idx": "No operations data available",
                    "nps_series": [],
                    "reviews_series": ["No operations data available"],
                },
                redactions,
            )

        payload = dict(ops)
        payload.setdefault("nps_series", [])
        reviews = payload.get("reviews_series", [])
        sanitised_reviews: List[str] = []
        for review in reviews:
            text = str(review)
            new_text, review_redactions = self._strip_pii(text)
            if review_redactions:
                self.logger.info(
                    "review_redacted",
                    extra={"original": text, "redactions": review_redactions},
                )
            redactions += review_redactions
            sanitised_reviews.append(new_text)
        payload["reviews_series"] = sanitised_reviews
        return payload, redactions

    def _normalise_state_pack(self, state_pack: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if not state_pack:
            return {
                "code": None,
                "changes": [
                    {
                        "section": "No state policy changes provided",
                        "setting": "—",
                        "current": "—",
                        "proposed": "—",
                    }
                ],
            }
        payload = dict(state_pack)
        payload.setdefault("changes", [])
        if not payload["changes"]:
            payload["changes"].append(
                {
                    "section": "No state policy changes provided",
                    "setting": "—",
                    "current": "—",
                    "proposed": "—",
                }
            )
        return payload

    def _strip_pii(self, text: str) -> tuple[str, int]:
        redactions = 0
        cleaned = _EMAIL_RE.sub("[REDACTED EMAIL]", text)
        redactions += len(_EMAIL_RE.findall(text))
        cleaned_phones = _PHONE_RE.sub("[REDACTED PHONE]", cleaned)
        redactions += len(_PHONE_RE.findall(cleaned))
        return cleaned_phones, redactions
