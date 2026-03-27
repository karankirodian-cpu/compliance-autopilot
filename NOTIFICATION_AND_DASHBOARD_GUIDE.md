# Compliance Autopilot - Notification & Dashboard System

## Overview

This project includes two major subsystems:

1. **Notification Service** - Automated email system for compliance alerts
2. **Dashboard & Reporting** - Real-time compliance tracking and analytics

## Directory Structure

```
app/
├── services/
│   ├── notification_service.py    # Email notification system
│   └── compliance_service.py       # Compliance data operations
├── api/
│   └── routes/
│       ├── dashboard.py            # Dashboard API endpoints
│       └── reports.py              # Reporting analytics endpoints
├── templates/
│   ├── dashboard.html              # Main dashboard UI
│   ├── new_circular_notification.html
│   ├── action_item_assignment.html
│   ├── action_item_reminder.html
│   ├── action_item_overdue.html
│   └── compliance_status_report.html
├── models/
│   └── database.py                 # Database models
└── main.py                         # FastAPI application
```

---

## 🔔 Notification Service

### Purpose
Sends automated email notifications to compliance teams for:
- New RBI circulars with impact assessment
- Action item assignments
- Deadline reminders
- Overdue item alerts
- Weekly/monthly compliance status reports

### Setup

1. **Install dependencies (already in requirements.txt)**
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Configure SMTP (in .env)**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-app-password  # Use Gmail App Password, not regular password
   DASHBOARD_URL=http://localhost:8000
   ```

3. **For Gmail:**
   - Enable 2-factor authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use the 16-character app password

### Usage

```python
from app.services.notification_service import NotificationService
from app.models.database import SessionLocal, RBICircular, Product, ActionItem
import os

# Initialize service
notifier = NotificationService(
    smtp_host=os.getenv("SMTP_HOST"),
    smtp_port=int(os.getenv("SMTP_PORT")),
    sender_email=os.getenv("SENDER_EMAIL"),
    sender_password=os.getenv("SENDER_PASSWORD"),
)

# Example 1: Notify about new circular
circular = db.query(RBICircular).first()
affected_products = db.query(Product).filter(Product.id.in_([1, 2])).all()
recipients = ["compliance@company.com", "manager@company.com"]

notifier.notify_new_circular(circular, affected_products, recipients)


# Example 2: Notify action item assignment
action_item = db.query(ActionItem).first()
product = db.query(Product).filter(Product.id == action_item.product_id).first()

notifier.notify_action_item_assignment(
    action_item=action_item,
    circular=circular,
    product=product,
    recipient_email="team-member@company.com"
)


# Example 3: Send deadline reminder
from datetime import datetime, timedelta

overdue_count = (action_item.due_date - datetime.utcnow()).days
notifier.notify_action_item_reminder(
    action_item=action_item,
    circular=circular,
    days_until_due=overdue_count,
    recipient_email="team-member@company.com"
)


# Example 4: Notify overdue items
notifier.notify_action_item_overdue(
    action_item=action_item,
    circular=circular,
    recipient_email="manager@company.com"
)


# Example 5: Send compliance status report
summary = {
    "total_circulars": 150,
    "pending_circulars": 5,
    "action_items_pending": 25,
    "action_items_completed": 100,
    "action_items_overdue": 3,
    "critical_items": 2,
}

notifier.notify_compliance_status_report(
    summary=summary,
    recipient_emails=["director@company.com", "compliance-lead@company.com"]
)
```

### Email Templates

5 professional HTML email templates included:

| Template | Purpose | Recipients |
|----------|---------|------------|
| `new_circular_notification.html` | Alert on new RBI circular | Compliance teams with affected products |
| `action_item_assignment.html` | Assign compliance task | Individual team member |
| `action_item_reminder.html` | Deadline approaching | Assignee |
| `action_item_overdue.html` | Item past due date | Assignee + manager |
| `compliance_status_report.html` | Weekly summary | Leadership |

---

## 📊 Dashboard & Reporting

### Dashboard Features

The interactive dashboard provides:

✅ **Real-time Metrics**
- Total RBI circulars received
- Pending vs processed circulars
- Action items by status (pending, in-progress, completed, overdue)
- Compliance completion percentage

✅ **Status Tracking**
- Upcoming deadlines (30-day view)
- Overdue items requiring immediate attention
- Recent circulars
- Compliance by product category

✅ **Interactive UI**
- Click through to detailed views
- Priority-based color coding
- Responsive mobile design
- Real-time data refresh (every 5 minutes)

### API Endpoints

#### Dashboard Routes

**GET `/api/dashboard/summary`**
```json
{
  "total_circulars": 150,
  "pending_circulars": 5,
  "processed_circulars": 145,
  "total_action_items": 300,
  "pending_actions": 30,
  "in_progress_actions": 50,
  "completed_actions": 215,
  "overdue_actions": 5,
  "critical_items": 8,
  "high_priority_items": 15,
  "recent_circulars": 5
}
```

**GET `/api/dashboard/circulars`**
```
Query Parameters:
- skip (default: 0)
- limit (default: 20, max: 100)
- status (optional: pending, processing, analyzed, assigned, completed, archived)
- search (optional: search term)

Response: { circulars: [...], total: N, skip: N, limit: N }
```

**GET `/api/dashboard/action-items`**
```
Query Parameters:
- skip (default: 0)
- limit (default: 20, max: 100)
- status (optional: pending, in_progress, completed, overdue)
- priority (optional: critical, high, medium, low)
- assigned_to (optional: assignee name/email)
- overdue_only (optional: boolean)

Response: { action_items: [...], total: N }
```

**GET `/api/dashboard/upcoming-deadlines`**
```
Query Parameters:
- days (default: 30, range: 1-365)
- limit (default: 10, max: 50)

Response: { upcoming_deadlines: [...], count: N }
```

**GET `/api/dashboard/overdue-items`**
```
Query Parameters:
- limit (default: 10, max: 50)

Response: { overdue_items: [...], count: N }
```

**GET `/api/dashboard/compliance-by-category`**

Returns compliance metrics per product category with health status.

**GET `/api/dashboard/product-compliance/{product_id}`**

Get detailed compliance status for a specific product.

#### Reports Routes

**GET `/api/reports/compliance-trend`**
```
Query Parameters:
- days (default: 30, range: 7-365)

Returns daily compliance metrics - circulars processed, actions completed
```

**GET `/api/reports/compliance-matrix`**

Matrix showing compliance % for each product category with health status.

**GET `/api/reports/priority-distribution`**

Distribution of action items by priority level.

**GET `/api/reports/status-distribution`**

Distribution of action items by status.

**GET `/api/reports/team-performance`**

Performance metrics per assignee/team member.

**GET `/api/reports/circular-statistics`**

Statistics about RBI circulars received and processing.

**GET `/api/reports/export-report`**
```
Query Parameters:
- format (json or csv)
- days (default: 30)

Returns compliance report in requested format
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your SMTP and other settings
```

### 3. Initialize Database
```bash
python
from app.models.database import Base, engine
Base.metadata.create_all(bind=engine)
exit()
```

### 4. Run Application
```bash
python main.py
```

### 5. Access Dashboard
- Dashboard: `http://localhost:8000/`
- API Docs: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

---

## 📧 Integration Examples

### Trigger notifications on circular ingestion:

```python
from app.services.notification_service import NotificationService
from app.models.database import SessionLocal, RBICircular, Product

db = SessionLocal()
notifier = NotificationService(...)

# After processing a new circular
new_circular = # ... fetch from DB
affected_products = # ... query DB for affected products
recipients = [] # gather from product.compliance_contacts

notifier.notify_new_circular(new_circular, affected_products, recipients)
```

### Trigger reminders via Celery task:

```python
# tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from app.models.database import SessionLocal, ActionItem, ActionStatus

@shared_task
def send_deadline_reminders():
    db = SessionLocal()
    tomorrow = datetime.utcnow() + timedelta(days=1)
    
    items = db.query(ActionItem).filter(
        ActionItem.due_date.between(
            datetime.utcnow(),
            tomorrow + timedelta(days=1)
        ),
        ActionItem.status != ActionStatus.COMPLETED
    ).all()
    
    for item in items:
        days_left = (item.due_date - datetime.utcnow()).days
        notifier.notify_action_item_reminder(
            item, days_left, item.assigned_to
        )

# Run task daily: celery beat schedule
```

---

## 🔧 Customization

### Add custom email template
1. Create HTML file in `app/templates/`
2. Add method to `NotificationService` class
3. Use Jinja2 template rendering

### Modify dashboard metrics
Edit `ComplianceService.get_dashboard_summary()` in `compliance_service.py`

### Add new reports
Create new route in `app/api/routes/reports.py`

---

## 📋 Database Schema

Key models tracked:
- **RBICircular** - Received circulars
- **ActionItem** - Compliance tasks created
- **Product** - Financial products in portfolio
- **ImpactAssessment** - Circular impact per product
- **AlertRule** - Custom notification rules
- **AuditLog** - Compliance activity trail

---

## ⚠️ Important Notes

1. **Email Authentication**: Gmail requires App Password (16 characters), not regular password
2. **Jinja2 Templates**: All email templates use Jinja2 syntax for dynamic data
3. **Timezone**: All timestamps use UTC internally
4. **Rate Limiting**: Consider adding rate limiting for production
5. **Security**: Store sensitive data (SMTP password, API keys) in `.env`, never commit

---

## 🤝 Support

For issues or questions about:
- **Notification System**: Check `NotificationService` docstrings
- **Dashboard**: Review `ComplianceService` data retrieval methods
- **API**: Check endpoint docstrings and Swagger docs at `/docs`

---

## 📝 License

Compliance Autopilot - 2026
