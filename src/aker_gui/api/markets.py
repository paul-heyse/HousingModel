"""
Market API endpoints for the GUI application.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session


# Simple session dependency for now
def get_session():
    """Get database session - placeholder implementation."""
    # This would normally connect to the database
    # For now, return a mock session
    from unittest.mock import MagicMock
    return MagicMock()
# Placeholder - MarketService would be implemented in aker_markets module
class MarketService:
    def __init__(self, session):
        self.session = session

    def list_markets(self, limit=100, offset=0):
        return []

    def get_market(self, msa_id):
        return None

    def get_market_scores(self, msa_id):
        return None

    def search_markets(self, query, limit=20):
        return []

router = APIRouter()


@router.get("/")
async def list_markets(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    """List all markets with pagination."""
    try:
        service = MarketService(db)
        markets = service.list_markets(limit=limit, offset=offset)
        return {
            "markets": markets,
            "total": len(markets),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list markets: {str(e)}")


@router.get("/{msa_id}")
async def get_market(
    msa_id: str,
    db: Session = Depends(get_session),
):
    """Get a specific market by MSA ID."""
    try:
        service = MarketService(db)
        market = service.get_market(msa_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        return market
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market: {str(e)}")


@router.get("/{msa_id}/scores")
async def get_market_scores(
    msa_id: str,
    db: Session = Depends(get_session),
):
    """Get detailed market scores for a specific MSA."""
    try:
        service = MarketService(db)
        scores = service.get_market_scores(msa_id)
        if not scores:
            raise HTTPException(status_code=404, detail="Market scores not found")
        return scores
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market scores: {str(e)}")


@router.post("/{msa_id}/refresh")
async def refresh_market_data(
    msa_id: str,
    db: Session = Depends(get_session),
):
    """Trigger a refresh of market data for a specific MSA."""
    try:
        _ = MarketService(db)
        # This would trigger the market scoring pipeline once implemented
        result = {"message": f"Market refresh triggered for {msa_id}", "status": "pending"}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh market: {str(e)}")


@router.get("/search")
async def search_markets(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
):
    """Search markets by name or MSA ID."""
    try:
        service = MarketService(db)
        markets = service.search_markets(query, limit=limit)
        return {
            "query": query,
            "results": markets,
            "total": len(markets),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search markets: {str(e)}")
