from __future__ import annotations

import json
import csv
import io
from datetime import datetime, date
from typing import Dict, List, Any, Optional

from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import pandas as pd

from aker_core.ops import reputation_index, pricing_rules
from aker_core.database import get_session


def get_reputation_data(asset_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, sources: Optional[str] = None) -> Dict[str, Any]:
    """Get reputation data for an asset."""
    session = get_session()

    # Default date range: last 12 months
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start_date = (date.today().replace(year=date.today().year - 1)).isoformat()

    # Mock implementation - in real system would query database
    # This simulates the expected API response format
    reputation_data = {
        "reputation_idx": 78.5,
        "nps_series": [
            {"date": "2024-01-01", "nps": 25},
            {"date": "2024-02-01", "nps": 30},
            {"date": "2024-03-01", "nps": 28},
            {"date": "2024-04-01", "nps": 32},
            {"date": "2024-05-01", "nps": 35},
            {"date": "2024-06-01", "nps": 33},
            {"date": "2024-07-01", "nps": 38},
            {"date": "2024-08-01", "nps": 40},
            {"date": "2024-09-01", "nps": 42},
            {"date": "2024-10-01", "nps": 45},
            {"date": "2024-11-01", "nps": 43},
            {"date": "2024-12-01", "nps": 47}
        ],
        "reviews_series": [
            {"date": "2024-01-01", "rating": 4.2, "volume": 15},
            {"date": "2024-02-01", "rating": 4.1, "volume": 18},
            {"date": "2024-03-01", "rating": 4.3, "volume": 22},
            {"date": "2024-04-01", "rating": 4.0, "volume": 16},
            {"date": "2024-05-01", "rating": 4.4, "volume": 25},
            {"date": "2024-06-01", "rating": 4.2, "volume": 20},
            {"date": "2024-07-01", "rating": 4.5, "volume": 28},
            {"date": "2024-08-01", "rating": 4.3, "volume": 24},
            {"date": "2024-09-01", "rating": 4.6, "volume": 32},
            {"date": "2024-10-01", "rating": 4.4, "volume": 29},
            {"date": "2024-11-01", "rating": 4.3, "volume": 26},
            {"date": "2024-12-01", "rating": 4.5, "volume": 31}
        ],
        "pricing_rules": {
            "max_concession_days": 7,
            "floor_price_pct": 5.0,
            "premium_cap_pct": 8.0
        }
    }

    return reputation_data


def process_csv_upload(file) -> Dict[str, Any]:
    """Process CSV upload and validate data."""
    if not file:
        return {"error": "No file provided"}

    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))

        # Validate and process rows
        ingested = 0
        rejected = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
            try:
                # Validate required fields
                if not row.get('date') or not row.get('source') or not row.get('rating') or not row.get('text'):
                    errors.append({
                        "row": row_num,
                        "error": "Missing required field (date, source, rating, or text)"
                    })
                    rejected += 1
                    continue

                # Validate rating (1-5)
                rating = float(row['rating'])
                if not 1.0 <= rating <= 5.0:
                    errors.append({
                        "row": row_num,
                        "error": f"Rating {rating} outside valid range (1.0-5.0)"
                    })
                    rejected += 1
                    continue

                # Validate date format
                try:
                    datetime.strptime(row['date'], '%Y-%m-%d')
                except ValueError:
                    errors.append({
                        "row": row_num,
                        "error": f"Invalid date format: {row['date']} (expected YYYY-MM-DD)"
                    })
                    rejected += 1
                    continue

                # Validate text length
                if len(row['text']) < 10:
                    errors.append({
                        "row": row_num,
                        "error": f"Review text too short: {len(row['text'])} characters (minimum 10)"
                    })
                    rejected += 1
                    continue

                # Process valid row
                ingested += 1

                # In real implementation, would save to database
                # For now, just count successful rows

            except Exception as e:
                errors.append({
                    "row": row_num,
                    "error": f"Processing error: {str(e)}"
                })
                rejected += 1

        # Limit error reporting to first 5 errors
        sample_errors = errors[:5]

        return {
            "ingested": ingested,
            "rejected": rejected,
            "sample_errors": sample_errors,
            "total_rows": ingested + rejected
        }

    except Exception as e:
        return {"error": f"File processing failed: {str(e)}"}


def get_pricing_preview(asset_id: str, reputation_idx: float) -> Dict[str, Any]:
    """Get pricing preview for hypothetical reputation index."""
    # Calculate pricing rules based on reputation index
    pricing = pricing_rules(reputation_idx)

    return {
        "guardrails": pricing,
        "based_on_reputation": reputation_idx,
        "asset_id": asset_id
    }


def register_ops_api(app):
    """Register ops API endpoints."""

    @app.route('/api/ops/reputation', methods=['GET'])
    def api_get_reputation():
        """Get reputation data for an asset."""
        asset_id = request.args.get('asset_id')
        if not asset_id:
            return jsonify({"error": "asset_id parameter required"}), 400

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sources = request.args.get('sources')

        try:
            data = get_reputation_data(asset_id, start_date, end_date, sources)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/ops/reviews/upload', methods=['POST'])
    def api_upload_reviews():
        """Upload and process CSV review data."""
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        try:
            result = process_csv_upload(file)
            if "error" in result:
                return jsonify(result), 400
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/ops/pricing/preview', methods=['GET'])
    def api_pricing_preview():
        """Get pricing preview for hypothetical reputation index."""
        asset_id = request.args.get('asset_id')
        reputation_idx_str = request.args.get('reputation_idx')

        if not asset_id or not reputation_idx_str:
            return jsonify({"error": "asset_id and reputation_idx parameters required"}), 400

        try:
            reputation_idx = float(reputation_idx_str)
            if not 0 <= reputation_idx <= 100:
                return jsonify({"error": "reputation_idx must be between 0 and 100"}), 400

            preview = get_pricing_preview(asset_id, reputation_idx)
            return jsonify(preview)
        except ValueError:
            return jsonify({"error": "Invalid reputation_idx value"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
