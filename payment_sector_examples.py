"""
Examples: Working with Historic Payment Sector Circulars
"""

from app.models.database import (
    SessionLocal,
    RBICircular,
    ActionItem,
    CircularScope,
    ActionStatus,
    Priority,
)
from app.services.compliance_service import ComplianceService
from datetime import datetime, timedelta


# ============================================================================
# Example 1: Get all Payment Sector circulars
# ============================================================================
def get_payment_sector_overview():
    """
    Get a complete overview of Payment Gateway and Aggregator circulars
    """
    db = SessionLocal()
    try:
        summary = ComplianceService.get_payment_sector_summary(db)
        
        print("\n" + "="*70)
        print("PAYMENT SECTOR COMPLIANCE OVERVIEW")
        print("="*70)
        
        for scope_name, scope_data in summary.items():
            print(f"\n{scope_name.upper().replace('_', ' ')}:")
            print(f"  Total Circulars: {scope_data['total']}")
            print(f"\n  Recent Additions:")
            
            for circ in scope_data.get('recent', []):
                issue_date = circ['issue_date'].strftime('%d %b %Y') if circ['issue_date'] else 'N/A'
                print(f"    • {circ['circular_number']}: {circ['title']}")
                print(f"      Issue Date: {issue_date}\n")
    
    finally:
        db.close()


# ============================================================================
# Example 2: Filter circulars by payment gateway scope
# ============================================================================
def list_gateway_compliance_requirements():
    """
    List all Payment Gateway compliance requirements from historic circulars
    """
    db = SessionLocal()
    try:
        circulars, total = ComplianceService.get_circulars_by_scope(
            db,
            scope="payment_gateway",
            limit=10
        )
        
        print("\n" + "="*70)
        print(f"PAYMENT GATEWAY COMPLIANCE REQUIREMENTS ({total} circulars)")
        print("="*70)
        
        for c in circulars:
            print(f"\n📋 {c.circular_number}")
            print(f"   Title: {c.title}")
            print(f"   Issue Date: {c.issue_date.strftime('%d %b %Y') if c.issue_date else 'N/A'}")
            if c.description:
                print(f"   Details: {c.description[:200]}...")
            if c.keywords:
                print(f"   Keywords: {', '.join(c.keywords[:5])}")
    
    finally:
        db.close()


# ============================================================================
# Example 3: Filter circulars by payment aggregator scope
# ============================================================================
def list_aggregator_compliance_requirements():
    """
    List all Payment Aggregator compliance requirements from historic circulars
    """
    db = SessionLocal()
    try:
        circulars, total = ComplianceService.get_circulars_by_scope(
            db,
            scope="payment_aggregator",
            limit=10
        )
        
        print("\n" + "="*70)
        print(f"PAYMENT AGGREGATOR COMPLIANCE REQUIREMENTS ({total} circulars)")
        print("="*70)
        
        for c in circulars:
            print(f"\n📋 {c.circular_number}")
            print(f"   Title: {c.title}")
            print(f"   Issue Date: {c.issue_date.strftime('%d %b %Y') if c.issue_date else 'N/A'}")
            if c.description:
                print(f"   Details: {c.description[:200]}...")
            if c.related_scopes:
                print(f"   Related Areas: {', '.join(c.related_scopes)}")
    
    finally:
        db.close()


# ============================================================================
# Example 4: Search for specific compliance topics
# ============================================================================
def search_security_requirements():
    """
    Search for all security-related requirements across circulars
    """
    db = SessionLocal()
    try:
        keywords = ["security", "encryption", "authentication", "tokenization"]
        circulars, total = ComplianceService.search_circulars_by_keywords(
            db,
            keywords=keywords,
            limit=20
        )
        
        print("\n" + "="*70)
        print(f"SECURITY REQUIREMENTS (Found {total} relevant circulars)")
        print("="*70)
        
        for c in circulars:
            scope_display = f" ({c.scope.value.replace('_', ' ')})" if c.scope else " (General)"
            print(f"\n  • {c.circular_number}{scope_display}")
            print(f"    {c.title}")
    
    finally:
        db.close()


# ============================================================================
# Example 5: Auto-create action items from historic circulars
# ============================================================================
def create_action_items_from_payment_circulars(company_name: str = "Your Company"):
    """
    Automatically create high-priority action items from payment sector circulars
    for implementation and review
    """
    db = SessionLocal()
    try:
        # Get all Payment Gateway and Aggregator circulars
        gateway_circulars, _ = ComplianceService.get_circulars_by_scope(
            db, "payment_gateway", limit=50
        )
        
        aggregator_circulars, _ = ComplianceService.get_circulars_by_scope(
            db, "payment_aggregator", limit=50
        )
        
        all_circulars = gateway_circulars + aggregator_circulars
        
        print(f"\n🔄 Creating action items for {company_name}...")
        print(f"Processing {len(all_circulars)} payment sector circulars\n")
        
        created_actions = []
        
        for c in all_circulars:
            # Check if action already exists
            existing = db.query(ActionItem).filter(
                ActionItem.circular_id == c.id,
                ActionItem.title.like(f"%{c.circular_number}%")
            ).first()
            
            if existing:
                print(f"  ✓ Action already exists for {c.circular_number}")
                continue
            
            # Determine priority based on scope
            if c.scope == CircularScope.PAYMENT_GATEWAY:
                priority = Priority.HIGH
                assignee = f"payment-systems-team@{company_name.lower().replace(' ', '')}.com"
                days_until_due = 45
            elif c.scope == CircularScope.PAYMENT_AGGREGATOR:
                priority = Priority.HIGH
                assignee = f"payment-operations@{company_name.lower().replace(' ', '')}.com"
                days_until_due = 45
            else:
                priority = Priority.MEDIUM
                assignee = f"compliance-team@{company_name.lower().replace(' ', '')}.com"
                days_until_due = 60
            
            # Create action item
            action = ActionItem(
                circular_id=c.id,
                title=f"[{c.circular_number}] Implement: {c.title}",
                description=c.description or f"Compliance requirement from {c.circular_number}",
                assigned_to=assignee,
                status=ActionStatus.PENDING,
                priority=priority,
                due_date=datetime.utcnow() + timedelta(days=days_until_due),
            )
            
            db.add(action)
            created_actions.append({
                "circular": c.circular_number,
                "title": c.title,
                "priority": priority.value,
                "assignee": assignee
            })
        
        if created_actions:
            db.commit()
            print(f"\n✓ Created {len(created_actions)} action items:\n")
            
            for action in created_actions:
                print(f"  • [{action['circular']}]")
                print(f"    Title: {action['title'][:60]}...")
                print(f"    Priority: {action['priority'].upper()}")
                print(f"    Assigned to: {action['assignee']}\n")
        else:
            print("No new action items needed (all already exist)")
        
        db.commit()
    
    finally:
        db.close()


# ============================================================================
# Example 6: Generate compliance matrix for payment sector
# ============================================================================
def generate_payment_sector_compliance_matrix():
    """
    Generate a compliance matrix showing all payment sector requirements
    """
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("PAYMENT SECTOR COMPLIANCE MATRIX")
        print("="*80)
        
        scopes = [CircularScope.PAYMENT_GATEWAY, CircularScope.PAYMENT_AGGREGATOR]
        
        for scope in scopes:
            circulars, total = ComplianceService.get_circulars_by_scope(
                db, scope.value, limit=50
            )
            
            print(f"\n{scope.value.upper().replace('_', ' ')} - {total} Circulars")
            print("-" * 80)
            
            # Group by area
            areas = {}
            for c in circulars:
                area = c.related_scopes[0] if c.related_scopes else "General"
                if area not in areas:
                    areas[area] = []
                areas[area].append(c)
            
            for area, circulars_in_area in areas.items():
                print(f"\n  {area}:")
                for c in circulars_in_area:
                    years_old = (datetime.utcnow() - c.issue_date).days // 365 if c.issue_date else 0
                    print(f"    • {c.circular_number} ({c.issue_date.year if c.issue_date else 'N/A'})")
                    print(f"      {c.title}")
    
    finally:
        db.close()


# ============================================================================
# Example 7: Check compliance status by payment scope
# ============================================================================
def check_payment_compliance_status():
    """
    Check implementation status of payment sector requirements
    """
    db = SessionLocal()
    try:
        print("\n" + "="*70)
        print("PAYMENT SECTOR COMPLIANCE STATUS")
        print("="*70)
        
        # Get action items by scope
        from sqlalchemy import and_
        
        for scope_enum in [CircularScope.PAYMENT_GATEWAY, CircularScope.PAYMENT_AGGREGATOR]:
            # Get all actions for this scope
            actions = db.query(ActionItem).join(
                RBICircular, ActionItem.circular_id == RBICircular.id
            ).filter(RBICircular.scope == scope_enum).all()
            
            if not actions:
                print(f"\n{scope_enum.value.upper().replace('_', ' ')}: No actions found")
                continue
            
            total = len(actions)
            pending = sum(1 for a in actions if a.status == ActionStatus.PENDING)
            in_progress = sum(1 for a in actions if a.status == ActionStatus.IN_PROGRESS)
            completed = sum(1 for a in actions if a.status == ActionStatus.COMPLETED)
            overdue = sum(1 for a in actions if a.status == ActionStatus.OVERDUE)
            
            completion_pct = (completed / total * 100) if total > 0 else 0
            
            print(f"\n{scope_enum.value.upper().replace('_', ' ')}:")
            print(f"  Total Actions: {total}")
            print(f"  ✓ Completed: {completed} ({completion_pct:.1f}%)")
            print(f"  ⟳ In Progress: {in_progress}")
            print(f"  ○ Pending: {pending}")
            
            if overdue > 0:
                print(f"  🚨 Overdue: {overdue} ⚠️ ATTENTION REQUIRED")
    
    finally:
        db.close()


# ============================================================================
# Main - Run all examples
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("HISTORIC RBI CIRCULARS - PAYMENT SECTOR EXAMPLES")
    print("="*70)
    
    # Run examples
    get_payment_sector_overview()
    
    list_gateway_compliance_requirements()
    
    list_aggregator_compliance_requirements()
    
    search_security_requirements()
    
    create_action_items_from_payment_circulars("Your Company")
    
    generate_payment_sector_compliance_matrix()
    
    check_payment_compliance_status()
    
    print("\n" + "="*70)
    print("✓ All examples completed!")
    print("="*70)
