"""
Email and notification service for compliance alerts and reminders
"""
import asyncio
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import logging
from jinja2 import Environment, FileSystemLoader
import os
from sqlalchemy.orm import Session
from app.models.database import ActionItem, RBICircular, Product, ActionStatus, Priority

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending email notifications and alerts"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        template_dir: str = "app/templates",
    ):
        """
        Initialize notification service with SMTP configuration
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            sender_email: Sender email address
            sender_password: Sender email password
            template_dir: Directory containing email templates
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        
        # Initialize Jinja2 template environment
        template_path = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_path))
    
    def _create_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send email to recipients
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional fallback)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(to_emails)
            
            # Attach text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            server = self._create_connection()
            server.sendmail(self.sender_email, to_emails, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def notify_new_circular(
        self,
        circular: RBICircular,
        affected_products: List[Product],
        recipients: List[str],
    ) -> bool:
        """
        Notify teams about new RBI circular with impact
        
        Args:
            circular: RBICircular object
            affected_products: List of affected products
            recipients: List of recipient emails
        
        Returns:
            True if notification sent successfully
        """
        try:
            template = self.jinja_env.get_template("new_circular_notification.html")
            html_content = template.render(
                circular_number=circular.circular_number,
                title=circular.title,
                issue_date=circular.issue_date.strftime("%d %b %Y") if circular.issue_date else "N/A",
                effective_date=circular.effective_date.strftime("%d %b %Y") if circular.effective_date else "N/A",
                description=circular.description,
                affected_products=[p.name for p in affected_products],
                document_url=circular.document_url,
                dashboard_link=os.getenv("DASHBOARD_URL", "http://localhost:8000/dashboard"),
            )
            
            subject = f"🔔 RBI Circular Alert: {circular.circular_number} - {circular.title[:50]}"
            return self.send_email(recipients, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send new circular notification: {str(e)}")
            return False
    
    def notify_action_item_assignment(
        self,
        action_item: ActionItem,
        circular: RBICircular,
        product: Optional[Product],
        recipient_email: str,
    ) -> bool:
        """
        Notify assignee of new action item
        
        Args:
            action_item: ActionItem object
            circular: Related RBICircular
            product: Related Product (if any)
            recipient_email: Recipient email address
        
        Returns:
            True if notification sent successfully
        """
        try:
            template = self.jinja_env.get_template("action_item_assignment.html")
            html_content = template.render(
                action_title=action_item.title,
                description=action_item.description,
                circular_number=circular.circular_number,
                circular_title=circular.title,
                product_name=product.name if product else "Multiple/N/A",
                due_date=action_item.due_date.strftime("%d %b %Y") if action_item.due_date else "N/A",
                priority=action_item.priority.value.upper(),
                dashboard_link=os.getenv("DASHBOARD_URL", "http://localhost:8000/dashboard"),
                action_link=f"{os.getenv('DASHBOARD_URL', 'http://localhost:8000')}/action-items/{action_item.id}",
            )
            
            subject = f"📋 Action Item Assigned: {action_item.title[:50]} - {action_item.priority.value.upper()}"
            return self.send_email([recipient_email], subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send action item assignment notification: {str(e)}")
            return False
    
    def notify_action_item_reminder(
        self,
        action_item: ActionItem,
        circular: RBICircular,
        days_until_due: int,
        recipient_email: str,
    ) -> bool:
        """
        Remind assignee of upcoming deadline
        
        Args:
            action_item: ActionItem object
            circular: Related RBICircular
            days_until_due: Number of days until due date
            recipient_email: Recipient email address
        
        Returns:
            True if notification sent successfully
        """
        try:
            template = self.jinja_env.get_template("action_item_reminder.html")
            html_content = template.render(
                action_title=action_item.title,
                description=action_item.description,
                circular_number=circular.circular_number,
                due_date=action_item.due_date.strftime("%d %b %Y") if action_item.due_date else "N/A",
                days_until_due=days_until_due,
                priority=action_item.priority.value.upper(),
                status=action_item.status.value.upper(),
                dashboard_link=os.getenv("DASHBOARD_URL", "http://localhost:8000/dashboard"),
                action_link=f"{os.getenv('DASHBOARD_URL', 'http://localhost:8000')}/action-items/{action_item.id}",
            )
            
            subject = f"⏰ Reminder: Action Item Due in {days_until_due} Days - {action_item.title[:40]}"
            return self.send_email([recipient_email], subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send action item reminder: {str(e)}")
            return False
    
    def notify_action_item_overdue(
        self,
        action_item: ActionItem,
        circular: RBICircular,
        recipient_email: str,
    ) -> bool:
        """
        Alert assignee and stakeholders about overdue action item
        
        Args:
            action_item: ActionItem object (with status OVERDUE)
            circular: Related RBICircular
            recipient_email: Recipient email address
        
        Returns:
            True if notification sent successfully
        """
        try:
            template = self.jinja_env.get_template("action_item_overdue.html")
            days_overdue = (datetime.utcnow() - action_item.due_date).days if action_item.due_date else 0
            
            html_content = template.render(
                action_title=action_item.title,
                description=action_item.description,
                circular_number=circular.circular_number,
                due_date=action_item.due_date.strftime("%d %b %Y") if action_item.due_date else "N/A",
                days_overdue=days_overdue,
                priority=action_item.priority.value.upper(),
                dashboard_link=os.getenv("DASHBOARD_URL", "http://localhost:8000/dashboard"),
                action_link=f"{os.getenv('DASHBOARD_URL', 'http://localhost:8000')}/action-items/{action_item.id}",
            )
            
            subject = f"🚨 OVERDUE: Action Item - {action_item.title[:50]} ({days_overdue} days late)"
            return self.send_email([recipient_email], subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send overdue notification: {str(e)}")
            return False
    
    def notify_compliance_status_report(
        self,
        summary: Dict[str, Any],
        recipient_emails: List[str],
    ) -> bool:
        """
        Send weekly/monthly compliance status report
        
        Args:
            summary: Dictionary with compliance metrics and stats
            recipient_emails: List of recipient emails
        
        Returns:
            True if notification sent successfully
        """
        try:
            template = self.jinja_env.get_template("compliance_status_report.html")
            html_content = template.render(
                report_date=datetime.utcnow().strftime("%d %b %Y"),
                total_circulars=summary.get("total_circulars", 0),
                pending_circulars=summary.get("pending_circulars", 0),
                action_items_pending=summary.get("action_items_pending", 0),
                action_items_completed=summary.get("action_items_completed", 0),
                action_items_overdue=summary.get("action_items_overdue", 0),
                critical_items=summary.get("critical_items", 0),
                dashboard_link=os.getenv("DASHBOARD_URL", "http://localhost:8000/dashboard"),
            )
            
            subject = f"📊 Compliance Status Report - {datetime.utcnow().strftime('%B %d, %Y')}"
            return self.send_email(recipient_emails, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send compliance status report: {str(e)}")
            return False
