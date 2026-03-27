"""
Reports API routes for compliance analytics and reporting
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List
from app.models.database import (
    SessionLocal,
    RBICircular,
    ActionItem,
    Product,
    CircularStatus,
    ActionStatus,
    Priority,
    ProductCategory,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/compliance-trend")
def get_compliance_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Get compliance trend over time
    
    Query Parameters:
        - days: Number of days to analyze (default: 30)
    
    Returns:
        Daily compliance metrics showing progress over time
    """
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Generate daily breakdown
        daily_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # Count circulars processed on this date
            circulars_processed = db.query(func.count(RBICircular.id)).filter(
                RBICircular.processed_at >= datetime.combine(current_date, datetime.min.time()),
                RBICircular.processed_at <= datetime.combine(current_date, datetime.max.time()),
            ).scalar() or 0
            
            # Count actions completed on this date
            actions_completed = db.query(func.count(ActionItem.id)).filter(
                ActionItem.completed_at >= datetime.combine(current_date, datetime.min.time()),
                ActionItem.completed_at <= datetime.combine(current_date, datetime.max.time()),
                ActionItem.status == ActionStatus.COMPLETED,
            ).scalar() or 0
            
            # Total pending actions as of this date
            total_actions = db.query(func.count(ActionItem.id)).filter(
                ActionItem.created_at <= datetime.combine(current_date, datetime.max.time()),
            ).scalar() or 0
            
            completed_actions = db.query(func.count(ActionItem.id)).filter(
                ActionItem.created_at <= datetime.combine(current_date, datetime.max.time()),
                ActionItem.status == ActionStatus.COMPLETED,
                ActionItem.completed_at <= datetime.combine(current_date, datetime.max.time()),
            ).scalar() or 0
            
            compliance_pct = (completed_actions / total_actions * 100) if total_actions > 0 else 0
            
            daily_data.append({
                "date": current_date.isoformat(),
                "circulars_processed": circulars_processed,
                "actions_completed": actions_completed,
                "compliance_percentage": round(compliance_pct, 2),
            })
            
            current_date += timedelta(days=1)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_data": daily_data,
        }
    except Exception as e:
        logger.error(f"Error generating compliance trend: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance trend")


@router.get("/compliance-matrix")
def get_compliance_matrix(db: Session = Depends(get_db)):
    """
    Get compliance matrix across product categories and circular types
    
    Returns:
        Matrix showing compliance % for each product category
    """
    try:
        categories = [c for c in ProductCategory if c != ProductCategory.ALL]
        matrix = []
        
        for category in categories:
            products = db.query(Product).filter(
                Product.category == category
            ).all()
            
            total_actions = 0
            completed_actions = 0
            critical_items = 0
            overdue_items = 0
            
            for product in products:
                actions = db.query(ActionItem).filter(
                    ActionItem.product_id == product.id
                ).all()
                
                total_actions += len(actions)
                completed_actions += sum(1 for a in actions if a.status == ActionStatus.COMPLETED)
                critical_items += sum(1 for a in actions if a.priority == Priority.CRITICAL)
                overdue_items += sum(
                    1 for a in actions 
                    if a.due_date and a.due_date < datetime.utcnow() and a.status != ActionStatus.COMPLETED
                )
            
            compliance_pct = (completed_actions / total_actions * 100) if total_actions > 0 else 0
            
            matrix.append({
                "category": category.value,
                "products_count": len(products),
                "total_actions": total_actions,
                "completed": completed_actions,
                "compliance_percentage": round(compliance_pct, 2),
                "critical_items": critical_items,
                "overdue_items": overdue_items,
                "health_status": "Good" if compliance_pct >= 80 else "Fair" if compliance_pct >= 50 else "Poor",
            })
        
        return {
            "matrix": sorted(matrix, key=lambda x: x["compliance_percentage"], reverse=True),
            "overall_compliance": round(
                sum(m["compliance_percentage"] for m in matrix) / len(matrix), 2
            ) if matrix else 0,
        }
    except Exception as e:
        logger.error(f"Error generating compliance matrix: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance matrix")


@router.get("/priority-distribution")
def get_priority_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of action items by priority level
    
    Returns:
        Count and percentage of items at each priority level
    """
    try:
        total = db.query(func.count(ActionItem.id)).scalar() or 0
        
        priorities = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        for priority in Priority:
            count = db.query(func.count(ActionItem.id)).filter(
                ActionItem.priority == priority
            ).scalar() or 0
            priorities[priority.value] = count
        
        return {
            "total_items": total,
            "by_priority": {
                priority: {
                    "count": count,
                    "percentage": round(count / total * 100, 2) if total > 0 else 0,
                }
                for priority, count in priorities.items()
            },
        }
    except Exception as e:
        logger.error(f"Error generating priority distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate priority distribution")


@router.get("/status-distribution")
def get_status_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of action items by status
    
    Returns:
        Count and percentage of items at each status
    """
    try:
        total = db.query(func.count(ActionItem.id)).scalar() or 0
        
        statuses = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "overdue": 0,
        }
        
        for status in ActionStatus:
            count = db.query(func.count(ActionItem.id)).filter(
                ActionItem.status == status
            ).scalar() or 0
            statuses[status.value] = count
        
        return {
            "total_items": total,
            "by_status": {
                status: {
                    "count": count,
                    "percentage": round(count / total * 100, 2) if total > 0 else 0,
                }
                for status, count in statuses.items()
            },
        }
    except Exception as e:
        logger.error(f"Error generating status distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate status distribution")


@router.get("/team-performance")
def get_team_performance(db: Session = Depends(get_db)):
    """
    Get performance metrics by team/assignee
    
    Returns:
        Completion rates and metrics per assignee
    """
    try:
        # Get all unique assignees
        assignees = db.query(ActionItem.assigned_to).distinct().all()
        
        team_stats = []
        for (assignee,) in assignees:
            if not assignee:
                continue
            
            total = db.query(func.count(ActionItem.id)).filter(
                ActionItem.assigned_to == assignee
            ).scalar() or 0
            
            completed = db.query(func.count(ActionItem.id)).filter(
                ActionItem.assigned_to == assignee,
                ActionItem.status == ActionStatus.COMPLETED,
            ).scalar() or 0
            
            overdue = db.query(func.count(ActionItem.id)).filter(
                ActionItem.assigned_to == assignee,
                ActionItem.due_date < datetime.utcnow(),
                ActionItem.status != ActionStatus.COMPLETED,
            ).scalar() or 0
            
            critical_assigned = db.query(func.count(ActionItem.id)).filter(
                ActionItem.assigned_to == assignee,
                ActionItem.priority == Priority.CRITICAL,
            ).scalar() or 0
            
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            team_stats.append({
                "assignee": assignee,
                "total_assigned": total,
                "completed": completed,
                "completion_rate": round(completion_rate, 2),
                "overdue_count": overdue,
                "critical_items": critical_assigned,
            })
        
        return {
            "team_members": sorted(team_stats, key=lambda x: x["completion_rate"], reverse=True),
            "average_completion_rate": round(
                sum(ts["completion_rate"] for ts in team_stats) / len(team_stats), 2
            ) if team_stats else 0,
        }
    except Exception as e:
        logger.error(f"Error generating team performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate team performance")


@router.get("/circular-statistics")
def get_circular_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about RBI circulars received and processed
    
    Returns:
        Circular processing metrics and trends
    """
    try:
        total_circulars = db.query(func.count(RBICircular.id)).scalar() or 0
        
        statuses = {}
        for status in CircularStatus:
            count = db.query(func.count(RBICircular.id)).filter(
                RBICircular.status == status
            ).scalar() or 0
            statuses[status.value] = count
        
        # Circulars in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent = db.query(func.count(RBICircular.id)).filter(
            RBICircular.issue_date >= thirty_days_ago
        ).scalar() or 0
        
        # Average impact per circular
        total_impacts = db.query(func.count(RBICircular.action_items)).scalar() or 0
        avg_impact = (total_impacts / total_circulars) if total_circulars > 0 else 0
        
        return {
            "total_circulars": total_circulars,
            "by_status": statuses,
            "recent_30_days": recent,
            "average_action_items_per_circular": round(avg_impact, 2),
        }
    except Exception as e:
        logger.error(f"Error generating circular statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate circular statistics")


@router.get("/export-report")
def export_compliance_report(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """
    Export compliance report in specified format
    
    Query Parameters:
        - format: Export format (json or csv)
        - days: Period to report on (default: 30)
    
    Returns:
        Comprehensive compliance report
    """
    try:
        # Gather all report data
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "circulars": db.query(func.count(RBICircular.id)).scalar() or 0,
            "action_items": db.query(func.count(ActionItem.id)).scalar() or 0,
            "completed": db.query(func.count(ActionItem.id)).filter(
                ActionItem.status == ActionStatus.COMPLETED
            ).scalar() or 0,
            "overdue": db.query(func.count(ActionItem.id)).filter(
                ActionItem.due_date < datetime.utcnow(),
                ActionItem.status != ActionStatus.COMPLETED,
            ).scalar() or 0,
        }
        
        summary["compliance_percentage"] = (
            summary["completed"] / summary["action_items"] * 100
        ) if summary["action_items"] > 0 else 0
        
        if format == "json":
            return JSONResponse(content=summary)
        elif format == "csv":
            # Generate CSV export
            csv_content = "Metric,Value\n"
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    csv_content += f"{key},{value}\n"
            
            return JSONResponse(
                content={"data": csv_content, "filename": f"compliance_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
                headers={"Content-Disposition": "attachment; filename=compliance_report.csv"},
            )
    except Exception as e:
        logger.error(f"Error exporting compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export report")
