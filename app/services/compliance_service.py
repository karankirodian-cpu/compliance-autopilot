"""
Compliance service for retrieving and aggregating compliance data
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.database import (
    RBICircular,
    ActionItem,
    Product,
    ImpactAssessment,
    ComplianceTracker,
    CircularStatus,
    CircularScope,
    ActionStatus,
    Priority,
    ProductCategory,
)
import logging

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for compliance data operations and aggregations"""
    
    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict[str, Any]:
        """
        Get overall compliance dashboard summary
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with key compliance metrics
        """
        try:
            # Count circulars by status
            total_circulars = db.query(RBICircular).count()
            pending_circulars = db.query(RBICircular).filter(
                RBICircular.status == CircularStatus.PENDING
            ).count()
            processed_circulars = db.query(RBICircular).filter(
                RBICircular.status == CircularStatus.ANALYZED
            ).count()
            
            # Count action items by status
            total_actions = db.query(ActionItem).count()
            pending_actions = db.query(ActionItem).filter(
                ActionItem.status == ActionStatus.PENDING
            ).count()
            in_progress_actions = db.query(ActionItem).filter(
                ActionItem.status == ActionStatus.IN_PROGRESS
            ).count()
            completed_actions = db.query(ActionItem).filter(
                ActionItem.status == ActionStatus.COMPLETED
            ).count()
            overdue_actions = db.query(ActionItem).filter(
                ActionItem.status == ActionStatus.OVERDUE
            ).count()
            
            # Count by priority
            critical_items = db.query(ActionItem).filter(
                ActionItem.priority == Priority.CRITICAL
            ).count()
            high_priority_items = db.query(ActionItem).filter(
                ActionItem.priority == Priority.HIGH
            ).count()
            
            # Recent circulars
            recent_circulars = db.query(RBICircular).order_by(
                RBICircular.issue_date.desc()
            ).limit(5).all()
            
            return {
                "total_circulars": total_circulars,
                "pending_circulars": pending_circulars,
                "processed_circulars": processed_circulars,
                "total_action_items": total_actions,
                "pending_actions": pending_actions,
                "in_progress_actions": in_progress_actions,
                "completed_actions": completed_actions,
                "overdue_actions": overdue_actions,
                "critical_items": critical_items,
                "high_priority_items": high_priority_items,
                "recent_circulars": len(recent_circulars),
            }
        except Exception as e:
            logger.error(f"Error retrieving dashboard summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_circulars(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        scope: Optional[str] = None,
        include_historic: bool = True,
    ) -> Tuple[List[RBICircular], int]:
        """
        Get paginated list of RBI circulars with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by circular status
            search: Search in title or description
            scope: Filter by circular scope (payment_gateway, payment_aggregator, etc.)
            include_historic: Include historic circulars
        
        Returns:
            Tuple of (circulars list, total count)
        """
        try:
            query = db.query(RBICircular)
            
            if status:
                query = query.filter(RBICircular.status == CircularStatus[status.upper()])
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        RBICircular.title.ilike(search_term),
                        RBICircular.description.ilike(search_term),
                        RBICircular.circular_number.ilike(search_term),
                    )
                )
            
            if scope:
                try:
                    scope_enum = CircularScope[scope.upper()]
                    query = query.filter(RBICircular.scope == scope_enum)
                except KeyError:
                    pass  # Invalid scope, ignore filter
            
            if not include_historic:
                query = query.filter(RBICircular.is_historic == False)
            
            total = query.count()
            circulars = query.order_by(RBICircular.issue_date.desc()).offset(skip).limit(limit).all()
            
            return circulars, total
        except Exception as e:
            logger.error(f"Error retrieving circulars: {str(e)}")
            return [], 0
    
    @staticmethod
    def get_action_items(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        overdue_only: bool = False,
    ) -> Tuple[List[ActionItem], int]:
        """
        Get paginated action items with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by action status
            priority: Filter by priority
            assigned_to: Filter by assignee
            overdue_only: Show only overdue items
        
        Returns:
            Tuple of (action items list, total count)
        """
        try:
            query = db.query(ActionItem)
            
            if status:
                query = query.filter(ActionItem.status == ActionStatus[status.upper()])
            
            if priority:
                query = query.filter(ActionItem.priority == Priority[priority.upper()])
            
            if assigned_to:
                query = query.filter(ActionItem.assigned_to.ilike(f"%{assigned_to}%"))
            
            if overdue_only:
                query = query.filter(
                    and_(
                        ActionItem.due_date < datetime.utcnow(),
                        ActionItem.status != ActionStatus.COMPLETED,
                    )
                )
            
            total = query.count()
            items = query.order_by(ActionItem.due_date.asc()).offset(skip).limit(limit).all()
            
            return items, total
        except Exception as e:
            logger.error(f"Error retrieving action items: {str(e)}")
            return [], 0
    
    @staticmethod
    def get_impact_assessment(
        db: Session,
        circular_id: int,
    ) -> List[ImpactAssessment]:
        """
        Get impact assessment for a circular
        
        Args:
            db: Database session
            circular_id: RBI Circular ID
        
        Returns:
            List of impact assessments
        """
        try:
            return db.query(ImpactAssessment).filter(
                ImpactAssessment.circular_id == circular_id
            ).all()
        except Exception as e:
            logger.error(f"Error retrieving impact assessment: {str(e)}")
            return []
    
    @staticmethod
    def get_product_compliance_status(
        db: Session,
        product_id: int,
    ) -> Dict[str, Any]:
        """
        Get compliance status for a specific product
        
        Args:
            db: Database session
            product_id: Product ID
        
        Returns:
            Dictionary with compliance metrics
        """
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {}
            
            # Get all action items for this product
            action_items = db.query(ActionItem).filter(
                ActionItem.product_id == product_id
            ).all()
            
            total = len(action_items)
            pending = sum(1 for ai in action_items if ai.status == ActionStatus.PENDING)
            in_progress = sum(1 for ai in action_items if ai.status == ActionStatus.IN_PROGRESS)
            completed = sum(1 for ai in action_items if ai.status == ActionStatus.COMPLETED)
            overdue = sum(1 for ai in action_items if ai.status == ActionStatus.OVERDUE)
            
            # Get related circulars
            circulars = db.query(RBICircular).join(
                ActionItem, ActionItem.circular_id == RBICircular.id
            ).filter(ActionItem.product_id == product_id).distinct().all()
            
            return {
                "product_id": product_id,
                "product_name": product.name,
                "category": product.category.value,
                "total_actions": total,
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed,
                "overdue": overdue,
                "related_circulars": len(circulars),
                "compliance_percentage": (completed / total * 100) if total > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error retrieving product compliance status: {str(e)}")
            return {}
    
    @staticmethod
    def get_compliance_by_category(
        db: Session,
    ) -> List[Dict[str, Any]]:
        """
        Get compliance summary by product category
        
        Args:
            db: Database session
        
        Returns:
            List of compliance summaries per category
        """
        try:
            categories = db.query(ProductCategory).all()
            results = []
            
            for category_enum in ProductCategory:
                if category_enum == ProductCategory.ALL:
                    continue
                
                products = db.query(Product).filter(
                    Product.category == category_enum
                ).all()
                
                total_actions = 0
                completed_actions = 0
                overdue_actions = 0
                
                for product in products:
                    actions = db.query(ActionItem).filter(
                        ActionItem.product_id == product.id
                    ).all()
                    total_actions += len(actions)
                    completed_actions += sum(
                        1 for a in actions if a.status == ActionStatus.COMPLETED
                    )
                    overdue_actions += sum(
                        1 for a in actions if a.status == ActionStatus.OVERDUE
                    )
                
                compliance_pct = (completed_actions / total_actions * 100) if total_actions > 0 else 0
                
                results.append({
                    "category": category_enum.value,
                    "total_products": len(products),
                    "total_actions": total_actions,
                    "completed_actions": completed_actions,
                    "overdue_actions": overdue_actions,
                    "compliance_percentage": compliance_pct,
                })
            
            return sorted(results, key=lambda x: x["compliance_percentage"], reverse=True)
        except Exception as e:
            logger.error(f"Error retrieving compliance by category: {str(e)}")
            return []
    
    @staticmethod
    def get_upcoming_deadlines(
        db: Session,
        days: int = 30,
        limit: int = 10,
    ) -> List[ActionItem]:
        """
        Get action items with upcoming deadlines
        
        Args:
            db: Database session
            days: Number of days to look ahead
            limit: Maximum items to return
        
        Returns:
            List of action items with upcoming deadlines
        """
        try:
            now = datetime.utcnow()
            future = now + timedelta(days=days)
            
            return db.query(ActionItem).filter(
                and_(
                    ActionItem.due_date >= now,
                    ActionItem.due_date <= future,
                    ActionItem.status != ActionStatus.COMPLETED,
                )
            ).order_by(ActionItem.due_date.asc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving upcoming deadlines: {str(e)}")
            return []
    
    @staticmethod
    def get_overdue_items(
        db: Session,
        limit: int = 10,
    ) -> List[ActionItem]:
        """
        Get overdue action items
        
        Args:
            db: Database session
            limit: Maximum items to return
        
        Returns:
            List of overdue action items
        """
        try:
            return db.query(ActionItem).filter(
                and_(
                    ActionItem.due_date < datetime.utcnow(),
                    ActionItem.status != ActionStatus.COMPLETED,
                )
            ).order_by(ActionItem.due_date.asc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving overdue items: {str(e)}")
            return []
    
    @staticmethod
    def get_circular_details(
        db: Session,
        circular_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed view of a circular with all related data
        
        Args:
            db: Database session
            circular_id: RBI Circular ID
        
        Returns:
            Dictionary with circular details or None
        """
        try:
            circular = db.query(RBICircular).filter(
                RBICircular.id == circular_id
            ).first()
            
            if not circular:
                return None
            
            # Get impact assessments
            impacts = db.query(ImpactAssessment).filter(
                ImpactAssessment.circular_id == circular_id
            ).all()
            
            # Get action items
            actions = db.query(ActionItem).filter(
                ActionItem.circular_id == circular_id
            ).all()
            
            return {
                "id": circular.id,
                "circular_number": circular.circular_number,
                "title": circular.title,
                "description": circular.description,
                "issue_date": circular.issue_date,
                "effective_date": circular.effective_date,
                "document_url": circular.document_url,
                "status": circular.status.value,
                "impacts": [
                    {
                        "product_id": imp.product_id,
                        "impact_level": imp.impact_level.value,
                        "deadline": imp.deadline,
                        "requirements": imp.compliance_requirements,
                    }
                    for imp in impacts
                ],
                "action_items": [
                    {
                        "id": ai.id,
                        "title": ai.title,
                        "assigned_to": ai.assigned_to,
                        "status": ai.status.value,
                        "priority": ai.priority.value,
                        "due_date": ai.due_date,
                    }
                    for ai in actions
                ],
            }
        except Exception as e:
            logger.error(f"Error retrieving circular details: {str(e)}")
            return None
    
    @staticmethod
    def get_circulars_by_scope(
        db: Session,
        scope: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[RBICircular], int]:
        """
        Get all circulars related to a specific scope/domain
        
        Args:
            db: Database session
            scope: CircularScope value (e.g., 'payment_gateway', 'payment_aggregator')
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            Tuple of (circulars list, total count)
        """
        try:
            scope_enum = CircularScope[scope.upper()]
            
            query = db.query(RBICircular).filter(
                or_(
                    RBICircular.scope == scope_enum,
                    RBICircular.related_scopes.contains(scope)
                )
            )
            
            total = query.count()
            circulars = query.order_by(RBICircular.issue_date.desc()).offset(skip).limit(limit).all()
            
            return circulars, total
        except KeyError:
            logger.error(f"Invalid scope: {scope}")
            return [], 0
        except Exception as e:
            logger.error(f"Error retrieving circulars by scope: {str(e)}")
            return [], 0
    
    @staticmethod
    def get_payment_sector_summary(db: Session) -> Dict[str, Any]:
        """
        Get summary of Payment Gateway and Aggregator circulars
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with payment sector metrics
        """
        try:
            # Count by scope
            gateway_count = db.query(RBICircular).filter(
                RBICircular.scope == CircularScope.PAYMENT_GATEWAY
            ).count()
            
            aggregator_count = db.query(RBICircular).filter(
                RBICircular.scope == CircularScope.PAYMENT_AGGREGATOR
            ).count()
            
            # Get recent additions
            recent_gateways = db.query(RBICircular).filter(
                RBICircular.scope == CircularScope.PAYMENT_GATEWAY
            ).order_by(RBICircular.issue_date.desc()).limit(3).all()
            
            recent_aggregators = db.query(RBICircular).filter(
                RBICircular.scope == CircularScope.PAYMENT_AGGREGATOR
            ).order_by(RBICircular.issue_date.desc()).limit(3).all()
            
            return {
                "payment_gateway": {
                    "total": gateway_count,
                    "recent": [
                        {
                            "circular_number": c.circular_number,
                            "title": c.title,
                            "issue_date": c.issue_date,
                        }
                        for c in recent_gateways
                    ],
                },
                "payment_aggregator": {
                    "total": aggregator_count,
                    "recent": [
                        {
                            "circular_number": c.circular_number,
                            "title": c.title,
                            "issue_date": c.issue_date,
                        }
                        for c in recent_aggregators
                    ],
                },
            }
        except Exception as e:
            logger.error(f"Error retrieving payment sector summary: {str(e)}")
            return {}
    
    @staticmethod
    def search_circulars_by_keywords(
        db: Session,
        keywords: List[str],
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[RBICircular], int]:
        """
        Search circulars by keywords
        
        Args:
            db: Database session
            keywords: List of keywords to search for
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            Tuple of (circulars list, total count)
        """
        try:
            query = db.query(RBICircular)
            
            # Search across multiple fields
            filters = []
            for keyword in keywords:
                search_term = f"%{keyword}%"
                filters.append(
                    or_(
                        RBICircular.title.ilike(search_term),
                        RBICircular.description.ilike(search_term),
                        RBICircular.circular_number.ilike(search_term),
                    )
                )
            
            if filters:
                query = query.filter(or_(*filters))
            
            total = query.count()
            circulars = query.order_by(RBICircular.issue_date.desc()).offset(skip).limit(limit).all()
            
            return circulars, total
        except Exception as e:
            logger.error(f"Error searching circulars: {str(e)}")
            return [], 0
