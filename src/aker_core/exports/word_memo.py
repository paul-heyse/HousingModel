"""Docx memo builder built on top of docxtpl."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import structlog
from docxtpl import DocxTemplate, InlineImage
from docx.image.image import Image
from docx.shared import Inches

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ImageDescriptor:
    """Descriptor describing an image placeholder in the memo."""

    key: str
    path: Path


class WordMemoBuilder:
    """Render IC-ready Word memos using docxtpl templates."""

    def __init__(self, template_path: Path | str) -> None:
        self.template_path = Path(template_path)

    def render(
        self,
        context: Mapping[str, Any],
        *,
        metadata: Optional[Mapping[str, Any]] = None,
        outdir: Optional[Path | str] = None,
    ) -> Path:
        """Render the memo to disk and return the output path."""
        self._ensure_template()

        doc = DocxTemplate(str(self.template_path))

        prepared_context, image_descriptors, missing_images = self._prepare_context(doc, context)
        inline = self._inline_image_factory(doc, image_descriptors, missing_images)

        render_context: Dict[str, Any] = dict(prepared_context)
        render_context.setdefault("InlineImage", inline)
        render_context.setdefault("Inches", Inches)
        render_context.setdefault("doc", doc)

        doc.render(render_context)

        output_dir = Path(outdir) if outdir else Path("exports/word")
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = self._output_filename(prepared_context)
        output_path = output_dir / file_name
        doc.save(output_path)

        tables_count = self._count_tables(prepared_context)
        image_count = sum(1 for descriptor in image_descriptors.values() if descriptor.path.exists())
        redactions = int(metadata.get("redactions", 0)) if metadata else 0

        for missing_key in missing_images:
            logger.warning("word_export_missing_image", key=missing_key, template=str(self.template_path))

        logger.info(
            "word_export_created",
            tables=tables_count,
            images=image_count,
            redactions=redactions,
            output=str(output_path),
        )

        return output_path

    def _ensure_template(self) -> None:
        if self.template_path.exists():
            return
        raise FileNotFoundError(f"Template not found at {self.template_path}")

    def _prepare_context(
        self,
        doc: DocxTemplate,
        context: Mapping[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, ImageDescriptor], set[str]]:
        prepared: Dict[str, Any] = dict(context)
        meta = prepared.pop("_memo_meta", None)
        if meta:
            logger.debug("memo_meta_consumed", meta=meta)
        images = prepared.get("images", {})
        if not isinstance(images, Mapping):
            raise ValueError("context['images'] must be a mapping of key->path")

        descriptors: Dict[str, ImageDescriptor] = {}
        missing: set[str] = set()
        for key, value in images.items():
            path = Path(value)
            descriptors[key] = ImageDescriptor(key=key, path=path)
            if not path.exists():
                missing.add(key)
                continue
            try:
                image = Image.from_file(str(path))
                dpi_x = (image.dpi or (0, 0))[0]
                if dpi_x and dpi_x < 300:
                    logger.warning("word_export_low_dpi", key=key, dpi=dpi_x)
                width_px = image.width
                reference_dpi = dpi_x or 300
                width_inches = width_px / reference_dpi if reference_dpi else None
                if width_inches and width_inches > 5.5:
                    logger.warning("word_export_wide_image", key=key, width_inches=width_inches)
            except Exception:  # pragma: no cover - metadata best effort
                logger.debug("word_export_image_metadata_unavailable", key=key)
        prepared["images"] = descriptors

        # Optional section defaults
        prepared.setdefault(
            "asset",
            {
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
            },
        )
        prepared.setdefault(
            "ops",
            {
                "reputation_idx": "No operations data available",
                "nps_series": [],
                "reviews_series": ["No operations data available"],
            },
        )
        prepared.setdefault(
            "state_pack",
            {
                "code": None,
                "changes": [
                    {
                        "section": "No state policy changes provided",
                        "setting": "—",
                        "current": "—",
                        "proposed": "—",
                    }
                ],
            },
        )

        return prepared, descriptors, missing

    def _inline_image_factory(
        self,
        doc: DocxTemplate,
        descriptors: Mapping[str, ImageDescriptor],
        missing: set[str],
    ):
        def _inline_image(_: Any, descriptor: Any, width: Any = None) -> Any:
            if isinstance(descriptor, ImageDescriptor):
                if descriptor.path.exists():
                    return InlineImage(doc, str(descriptor.path), width=width)
                missing.add(descriptor.key)
                return f"[IMAGE MISSING: {descriptor.key}]"
            if descriptor is None:
                return "[IMAGE MISSING: unknown]"
            path = Path(str(descriptor))
            if path.exists():
                return InlineImage(doc, str(path), width=width)
            placeholder_key = getattr(descriptor, "key", str(descriptor))
            missing.add(placeholder_key)
            return f"[IMAGE MISSING: {placeholder_key}]"

        return _inline_image

    def _output_filename(self, context: Mapping[str, Any]) -> str:
        msa = context.get("msa", {})
        msa_name = msa.get("name", "msa")
        created_at = context.get("created_at")
        if isinstance(created_at, datetime):
            timestamp = created_at.strftime("%Y%m%d%H%M%S")
        else:
            timestamp = str(created_at).replace(":", "").replace("-", "").replace("T", "")[:14]
        return f"aker_ic_memo_{msa_name}_{timestamp}.docx"

    def _count_tables(self, context: Mapping[str, Any]) -> int:
        tables = 0
        market_tables = context.get("market_tables", {})
        if isinstance(market_tables, Mapping):
            tables += sum(1 for rows in market_tables.values() if rows)
        risk = context.get("risk", {})
        if isinstance(risk, Mapping) and risk.get("multipliers"):
            tables += 1
        asset = context.get("asset", {})
        if isinstance(asset, Mapping) and asset.get("flags"):
            tables += 1
        state_pack = context.get("state_pack", {})
        if isinstance(state_pack, Mapping) and state_pack.get("changes"):
            tables += 1
        data_vintage = context.get("data_vintage", {})
        if data_vintage:
            tables += 1
        return tables


def to_word(
    context: Mapping[str, Any],
    *,
    template_path: Path | str = Path("templates/ic_memo.docx"),
    outdir: Optional[Path | str] = None,
) -> Path:
    """Convenience function mirroring the public API contract."""
    context_dict = dict(context)
    metadata = context_dict.pop("_memo_meta", {})
    builder = WordMemoBuilder(template_path)
    return builder.render(context_dict, metadata=metadata, outdir=outdir)
