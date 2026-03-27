"""
Dashboard API routes for compliance overview and status
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.services.compliance_service import ComplianceService
from app.models.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get overall compliance dashboard summary
    
    Returns:
        - total_circulars: Total RBI circulars received
        - pending_circulars: Circulars awaiting processing
        - processed_circulars: Circulars analyzed
        - total_action_items: Total action items created
        - pending_actions: Actions not started
        - in_progress_actions: Actions in progress
        - completed_actions: Completed actions
        - overdue_actions: Actions past due date
        - critical_items: Critical priority actions
        - high_priority_items: High priority actions
    """
    return ComplianceService.get_dashboard_summary(db)


@router.get("/circulars")
def get_circulars(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    include_historic: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of RBI circulars with optional filtering
    
    Query Parameters:
        - skip: Number of records to skip (default: 0)
        - limit: Maximum records to return (default: 20, max: 100)
        - status: Filter by status (pending, processing, analyzed, assigned, completed, archived)
        - search: Search term for title, description, or circular number
        - scope: Filter by scope (payment_gateway, payment_aggregator, etc.)
        - include_historic: Include historic circulars (default: true)
    
    Returns:
        - circulars: List of circular objects
        - total: Total count of matching circulars
    """
    circulars, total = ComplianceService.get_circulars(
        db, skip, limit, status, search, scope, include_historic
    )
    return {
        "circulars": [
            {
                "id": c.id,
                "circular_number": c.circular_number,
                "title": c.title,
                "issue_date": c.issue_date,
                "effective_date": c.effective_date,
                "status": c.status.value,
                "scope": c.scope.value if c.scope else None,
                "is_historic": c.is_historic,
                "document_url": c.document_url,
            }
            for c in circulars
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/circular/{circular_id}")
def get_circular_detail(circular_id: int, db: Session = Depends(get_db)):
    """
    Get detailed view of a specific circular
    
    Path Parameters:
        - circular_id: RBI Circular ID
    
    Returns:
        Circular object with impact assessments and action items
    """
    details = ComplianceService.get_circular_details(db, circular_id)
    if not details:
        raise HTTPException(status_code=404, detail="Circular not found")
    return details


@router.get("/action-items")
def get_action_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Get paginated action items with optional filtering
    
    Query Parameters:
        - skip: Number of records to skip
        - limit: Maximum records to return
        - status: Filter by status (pending, in_progress, completed, overdue)
        - priority: Filter by priority (critical, high, medium, low)
        - assigned_to: Filter by assignee name/email
        - overdue_only: Show only overdue items
    
    Returns:
        - action_items: List of action item objects
        - total: Total count of matching items
    """
    items, total = ComplianceService.get_action_items(
        db, skip, limit, status, priority, assigned_to, overdue_only
    )
    return {
        "action_items": [
            {
                "id": ai.id,
                "title": ai.title,
                "circular_id": ai.circular_id,
                "product_id": ai.product_id,
                "assigned_to": ai.assigned_to,
                "status": ai.status.value,
                "priority": ai.priority.value,
                "due_date": ai.due_date,
                "created_at": ai.created_at,
                "updated_at": ai.updated_at,
            }
            for ai in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/action-items/{action_id}")
def get_action_item_detail(action_id: int, db: Session = Depends(get_db)):
    """
    Get detailed view of a specific action item
    
    Path Parameters:
        - action_id: Action Item ID
    
    Returns:
        Action item object with full details
    """
    from app.models.database import ActionItem
    
    item = db.query(ActionItem).filter(ActionItem.id == action_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "circular_id": item.circular_id,
        "product_id": item.product_id,
        "assigned_to": item.assigned_to,
        "status": item.status.value,
        "priority": item.priority.value,
        "due_date": item.due_date,
        "completed_at": item.completed_at,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "reminder_sent": item.reminder_sent,
    }


@router.get("/compliance-by-category")
def get_compliance_by_category(db: Session = Depends(get_db)):
    """
    Get compliance summary grouped by product category
    
    Returns:
        List of compliance metrics per product category
    """
    return {
        "categories": ComplianceService.get_compliance_by_category(db)
    }


@router.get("/product-compliance/{product_id}")
def get_product_compliance(product_id: int, db: Session = Depends(get_db)):
    """
    Get compliance status for a specific product
    
    Path Parameters:
        - product_id: Product ID
    
    Returns:
        Compliance metrics for the product
    """
    status = ComplianceService.get_product_compliance_status(db, product_id)
    if not status:
        raise HTTPException(status_code=404, detail="Product not found")
    return status


@router.get("/upcoming-deadlines")
def get_upcoming_deadlines(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get action items with upcoming deadlines
    
    Query Parameters:
        - days: Number of days to look ahead (default: 30)
        - limit: Maximum items to return (default: 10)
    
    Returns:
        List of action items with upcoming deadlines
    """
    items = ComplianceService.get_upcoming_deadlines(db, days, limit)
    return {
        "upcoming_deadlines": [
            {
                "id": ai.id,
                "title": ai.title,
                "assigned_to": ai.assigned_to,
                "priority": ai.priority.value,
                "due_date": ai.due_date,
                "days_until_due": (ai.due_date - __import__("datetime").datetime.utcnow()).days if ai.due_date else None,
            }
            for ai in items
        ],
        "count": len(items),
    }


@router.get("/overdue-items")
def get_overdue_items(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get overdue action items requiring attention
    
    Query Parameters:
        - limit: Maximum items to return (default: 10)
    
    Returns:
        List of overdue action items
    """
    items = ComplianceService.get_overdue_items(db, limit)
    from datetime import datetime
    return {
        "overdue_items": [
            {
                "id": ai.id,
                "title": ai.title,
                "circular_id": ai.circular_id,
                "assigned_to": ai.assigned_to,
                "due_date": ai.due_date,
                "priority": ai.priority.value,
                "days_overdue": (datetime.utcnow() - ai.due_date).days if ai.due_date else None,
            }
            for ai in items
        ],
        "count": len(items),
    }


@router.get("/payment-sector-summary")
def get_payment_sector_summary(db: Session = Depends(get_db)):
    """
    Get summary of Payment Gateway and Payment Aggregator circulars
    
    Returns:
        Summary with counts and recent circulars for each scope
    """
    return ComplianceService.get_payment_sector_summary(db)


@router.get("/circulars-by-scope/{scope}")
def get_circulars_by_scope(
    scope: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all circulars for a specific scope
    
    Path Parameters:
        - scope: Circular scope (payment_gateway, payment_aggregator, etc.)
    
    Query Parameters:
        - skip: Number of records to skip
        - limit: Maximum records to return
    
    Returns:
        List of circulars for the scope
    """
    circulars, total = ComplianceService.get_circulars_by_scope(db, scope, skip, limit)
    return {
        "scope": scope,
        "circulars": [
            {
                "id": c.id,
                "circular_number": c.circular_number,
                "title": c.title,
                "issue_date": c.issue_date,
                "effective_date": c.effective_date,
                "status": c.status.value,
                "is_historic": c.is_historic,
            }
            for c in circulars
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/search-circulars")
def search_circulars(
    keywords: str = Query(..., description="Comma-separated keywords"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Search circulars by keywords
    
    Query Parameters:
        - keywords: Comma-separated search keywords
        - skip: Number of records to skip
        - limit: Maximum records to return
    
    Returns:
        List of matching circulars
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    circulars, total = ComplianceService.search_circulars_by_keywords(
        db, keyword_list, skip, limit
    )
    return {
        "keywords": keyword_list,
        "circulars": [
            {
                "id": c.id,
                "circular_number": c.circular_number,
                "title": c.title,
                "issue_date": c.issue_date,
                "scope": c.scope.value if c.scope else None,
            }
            for c in circulars
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
