"""
Integration examples and helper functions for using the notification and dashboard systems
"""

from datetime import datetime, timedelta
from app.services.notification_service import NotificationService
from app.services.compliance_service import ComplianceService
from app.models.database import (
    SessionLocal,
    RBICircular,
    ActionItem,
    Product,
    ImpactAssessment,
    CircularStatus,
    ActionStatus,
    Priority,
)
import os
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Process new circular and notify stakeholders
# ============================================================================
def process_circular_with_notifications(circular_id: int, notifier: NotificationService):
    """
    Process a new circular through impact assessment and notify affected teams
    
    Args:
        circular_id: ID of the RBICircular to process
        notifier: NotificationService instance
    """
    db = SessionLocal()
    try:
        # Get the circular
        circular = db.query(RBICircular).filter(
            RBICircular.id == circular_id
        ).first()
        
        if not circular:
            logger.error(f"Circular {circular_id} not found")
            return
        
        # Get impact assessments for this circular
        impacts = db.query(ImpactAssessment).filter(
            ImpactAssessment.circular_id == circular_id
        ).all()
        
        # Collect affected products and their compliance contacts
        affected_products = []
        recipients = set()
        
        for impact in impacts:
            product = db.query(Product).filter(
                Product.id == impact.product_id
            ).first()
            
            if product:
                affected_products.append(product)
                if product.compliance_contacts:
                    recipients.update(product.compliance_contacts)
        
        # Send notification
        if recipients:
            success = notifier.notify_new_circular(
                circular=circular,
                affected_products=affected_products,
                recipients=list(recipients)
            )
            
            if success:
                logger.info(f"Notified {len(recipients)} recipients about circular {circular_id}")
                circular.status = CircularStatus.ASSIGNED
                db.commit()
            else:
                logger.error(f"Failed to send notifications for circular {circular_id}")
    
    except Exception as e:
        logger.error(f"Error processing circular: {str(e)}")
    
    finally:
        db.close()


# ============================================================================
# Example 2: Auto-assign actions and notify assignees
# ============================================================================
def assign_and_notify_action_items(circular_id: int, notifier: NotificationService):
    """
    Create action items for a circular and immediately notify assignees
    
    Args:
        circular_id: ID of the RBICircular
        notifier: NotificationService instance
    """
    db = SessionLocal()
    try:
        circular = db.query(RBICircular).filter(
            RBICircular.id == circular_id
        ).first()
        
        if not circular:
            return
        
        # Get action items for this circular
        actions = db.query(ActionItem).filter(
            ActionItem.circular_id == circular_id,
            ActionItem.status == ActionStatus.PENDING
        ).all()
        
        # Notify each assignee
        for action in actions:
            product = None
            if action.product_id:
                product = db.query(Product).filter(
                    Product.id == action.product_id
                ).first()
            
            # Send assignment notification
            notifier.notify_action_item_assignment(
                action_item=action,
                circular=circular,
                product=product,
                recipient_email=action.assigned_to
            )
            
            logger.info(f"Notified {action.assigned_to} about action {action.id}")
    
    except Exception as e:
        logger.error(f"Error assigning actions: {str(e)}")
    
    finally:
        db.close()


# ============================================================================
# Example 3: Scheduled tasks for reminders and escalations
# ============================================================================
class ComplianceReminderScheduler:
    """
    Scheduler for sending deadline reminders and escalating overdue items
    Use with APScheduler or Celery Beat
    """
    
    def __init__(self, notifier: NotificationService):
        self.notifier = notifier
        self.db = SessionLocal()
    
    def send_deadline_reminders(self, days_ahead: int = 1):
        """
        Send reminders for items due in N days
        
        Args:
            days_ahead: Days until due date to send reminder
        """
        try:
            target_date = datetime.utcnow() + timedelta(days=days_ahead)
            start_date = target_date - timedelta(hours=1)
            end_date = target_date + timedelta(hours=1)
            
            # Find items due soon
            items = self.db.query(ActionItem).filter(
                ActionItem.due_date.between(start_date, end_date),
                ActionItem.status != ActionStatus.COMPLETED,
                ActionItem.reminder_sent == False
            ).all()
            
            for item in items:
                circular = self.db.query(RBICircular).filter(
                    RBICircular.id == item.circular_id
                ).first()
                
                days_until = (item.due_date - datetime.utcnow()).days
                
                if self.notifier.notify_action_item_reminder(
                    action_item=item,
                    circular=circular,
                    days_until_due=days_until,
                    recipient_email=item.assigned_to
                ):
                    item.reminder_sent = True
                    self.db.commit()
                    logger.info(f"Reminder sent for action {item.id}")
        
        except Exception as e:
            logger.error(f"Error sending reminders: {str(e)}")
    
    def escalate_overdue_items(self):
        """
        Find overdue items and escalate to managers
        """
        try:
            # Find overdue uncompleted items
            overdue_items = self.db.query(ActionItem).filter(
                ActionItem.due_date < datetime.utcnow(),
                ActionItem.status != ActionStatus.COMPLETED
            ).all()
            
            for item in overdue_items:
                # Update status if not already overdue
                if item.status != ActionStatus.OVERDUE:
                    item.status = ActionStatus.OVERDUE
                    self.db.commit()
                
                # Get circular info
                circular = self.db.query(RBICircular).filter(
                    RBICircular.id == item.circular_id
                ).first()
                
                # Send overdue notification
                self.notifier.notify_action_item_overdue(
                    action_item=item,
                    circular=circular,
                    recipient_email=item.assigned_to
                )
                
                logger.warning(f"Overdue action {item.id} escalated")
        
        except Exception as e:
            logger.error(f"Error escalating overdue items: {str(e)}")
    
    def send_weekly_compliance_report(self, recipient_emails: list):
        """
        Send weekly compliance status report to leadership
        
        Args:
            recipient_emails: List of email addresses for report recipients
        """
        try:
            summary = ComplianceService.get_dashboard_summary(self.db)
            
            self.notifier.notify_compliance_status_report(
                summary=summary,
                recipient_emails=recipient_emails
            )
            
            logger.info(f"Weekly report sent to {len(recipient_emails)} recipients")
        
        except Exception as e:
            logger.error(f"Error sending compliance report: {str(e)}")
    
    def close(self):
        """Close database session"""
        self.db.close()


# ============================================================================
# Example 4: Setup scheduler with APScheduler
# ============================================================================
def setup_compliance_scheduler(notifier: NotificationService):
    """
    Configure scheduled tasks for compliance notifications
    
    Usage:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        scheduler = BackgroundScheduler()
        setup_compliance_scheduler(notifier)
        scheduler.start()
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    reminder = ComplianceReminderScheduler(notifier)
    
    # Send reminders daily at 9 AM for items due tomorrow
    scheduler.add_job(
        func=reminder.send_deadline_reminders,
        kwargs={"days_ahead": 1},
        trigger="cron",
        hour=9,
        minute=0,
        id="daily_reminders"
    )
    
    # Check for overdue items every 4 hours
    scheduler.add_job(
        func=reminder.escalate_overdue_items,
        trigger="interval",
        hours=4,
        id="escalate_overdue"
    )
    
    # Send weekly report every Monday at 8 AM
    scheduler.add_job(
        func=reminder.send_weekly_compliance_report,
        kwargs={"recipient_emails": ["director@company.com", "compliance-lead@company.com"]},
        trigger="cron",
        day_of_week="mon",
        hour=8,
        minute=0,
        id="weekly_report"
    )
    
    scheduler.start()
    logger.info("Compliance scheduler started")
    
    return scheduler


# ============================================================================
# Example 5: Manual dashboard data generation
# ============================================================================
def generate_dashboard_snapshot(output_file: str = "dashboard_snapshot.json"):
    """
    Generate a complete dashboard data snapshot for inspection/debugging
    
    Args:
        output_file: Path to save JSON snapshot
    """
    import json
    
    db = SessionLocal()
    try:
        snapshot = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": ComplianceService.get_dashboard_summary(db),
            "compliance_by_category": ComplianceService.get_compliance_by_category(db),
            "upcoming_deadlines": [
                {
                    "id": item.id,
                    "title": item.title,
                    "due_date": item.due_date.isoformat() if item.due_date else None,
                    "assigned_to": item.assigned_to,
                    "priority": item.priority.value,
                }
                for item in ComplianceService.get_upcoming_deadlines(db, days=30)
            ],
            "overdue_items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "due_date": item.due_date.isoformat() if item.due_date else None,
                    "assigned_to": item.assigned_to,
                    "days_overdue": (datetime.utcnow() - item.due_date).days if item.due_date else 0,
                }
                for item in ComplianceService.get_overdue_items(db)
            ],
        }
        
        with open(output_file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)
        
        logger.info(f"Dashboard snapshot saved to {output_file}")
        return snapshot
    
    except Exception as e:
        logger.error(f"Error generating snapshot: {str(e)}")
    
    finally:
        db.close()


# ============================================================================
# Example 6: Database health check
# ============================================================================
def check_compliance_health(db_session=None):
    """
    Check health and consistency of compliance database
    
    Args:
        db_session: Optional database session (creates new one if not provided)
    
    Returns:
        Dictionary with health metrics
    """
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True
    
    try:
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": "healthy",
            "metrics": {}
        }
        
        # Count records
        health["metrics"]["total_circulars"] = db_session.query(RBICircular).count()
        health["metrics"]["total_action_items"] = db_session.query(ActionItem).count()
        health["metrics"]["total_products"] = db_session.query(Product).count()
        
        # Check for orphaned records
        orphaned_actions = db_session.query(ActionItem).filter(
            ~ActionItem.circular_id.in_(
                db_session.query(RBICircular.id)
            )
        ).count()
        
        if orphaned_actions > 0:
            health["database"] = "warning"
            health["warnings"] = [f"{orphaned_actions} orphaned action items"]
        
        # Check for very old pending items
        old_pending = db_session.query(ActionItem).filter(
            ActionItem.status == ActionStatus.PENDING,
            ActionItem.created_at < datetime.utcnow() - timedelta(days=90)
        ).count()
        
        if old_pending > 0:
            health["warnings"] = health.get("warnings", [])
            health["warnings"].append(f"{old_pending} items pending for 90+ days")
        
        logger.info(f"Health check: {health['database']}")
        return health
    
    finally:
        if close_session:
            db_session.close()


# ============================================================================
# Example 7: Bulk operations
# ============================================================================
def bulk_notify_product_owners(circular_id: int, notifier: NotificationService):
    """
    Send notifications to all product owners affected by a circular
    
    Args:
        circular_id: RBI Circular ID
        notifier: NotificationService instance
    """
    db = SessionLocal()
    try:
        circular = db.query(RBICircular).filter(
            RBICircular.id == circular_id
        ).first()
        
        if not circular:
            return
        
        # Get all affected products through impact assessments
        impacts = db.query(ImpactAssessment).filter(
            ImpactAssessment.circular_id == circular_id
        ).all()
        
        sent_count = 0
        for impact in impacts:
            product = db.query(Product).filter(
                Product.id == impact.product_id
            ).first()
            
            if product and product.compliance_contacts:
                success = notifier.notify_new_circular(
                    circular=circular,
                    affected_products=[product],
                    recipients=product.compliance_contacts
                )
                
                if success:
                    sent_count += len(product.compliance_contacts)
        
        logger.info(f"Sent {sent_count} notifications for circular {circular_id}")
    
    except Exception as e:
        logger.error(f"Error in bulk notification: {str(e)}")
    
    finally:
        db.close()
