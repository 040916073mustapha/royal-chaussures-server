"""Dashboard API — powers the Dark Theme analytics dashboard."""

import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

from app.database.models import SessionLocal
from app.database import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard/stats")
async def dashboard_stats(store_id: int = Query(1, description="Tenant store ID")):
    """Return dashboard aggregate stats for a store."""
    db = next(get_db())
    try:
        orders = crud.list_recent_orders(db, store_id, limit=1000)
        total_revenue = sum(o.total_price or 0 for o in orders)
        total_orders = len(orders)
        fulfilled = sum(1 for o in orders if o.fulfillment_status == "fulfilled")
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "fulfilled_orders": fulfilled,
            "pending_orders": total_orders - fulfilled,
            "currency": "DZD",
        }
    except Exception as e:
        logger.exception(f"[Dashboard] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/dashboard/recent-orders")
async def recent_orders(store_id: int = Query(1), limit: int = Query(10)):
    """Return recent orders for the dashboard table."""
    db = next(get_db())
    try:
        orders = crud.list_recent_orders(db, store_id, limit=limit)
        return [
            {
                "id": o.id,
                "shopify_order_id": o.shopify_order_id,
                "customer_name": o.customer_name,
                "total_price": o.total_price,
                "financial_status": o.financial_status,
                "fulfillment_status": o.fulfillment_status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]
    except Exception as e:
        logger.exception(f"[Dashboard] Recent orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/dashboard/conversations")
async def active_conversations(store_id: int = Query(1), limit: int = Query(20)):
    """Return active conversations for the live chat inbox."""
    db = next(get_db())
    try:
        convs = crud.list_active_conversations(db, store_id, limit=limit)
        return [
            {
                "id": c.id,
                "platform": c.platform,
                "last_message": c.last_message,
                "last_activity": c.last_activity.isoformat() if c.last_activity else None,
                "agent_handled": c.agent_handled,
            }
            for c in convs
        ]
    except Exception as e:
        logger.exception(f"[Dashboard] Conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
