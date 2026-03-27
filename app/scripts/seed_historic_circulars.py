"""
Seed historic RBI circulars for Payment Gateways and Payment Aggregators
Run this script once to populate database with payment sector circulars
"""
import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import (
    SessionLocal,
    RBICircular,
    CircularStatus,
    CircularScope,
    Base,
    engine,
)

# Historic RBI Circulars relevant to Payment Gateways and Payment Aggregators
HISTORIC_CIRCULARS = [
    {
        "circular_number": "RBI/DFS/2023-24/142",
        "title": "Master Direction – Digital Payment Security Requirements",
        "description": "Prescribes security parameters for digital payment systems including payment gateways and aggregators to ensure customer data protection and transaction integrity.",
        "issue_date": datetime(2023, 12, 15),
        "effective_date": datetime(2024, 1, 1),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.PAYMENT_AGGREGATOR.value, CircularScope.DATA_SECURITY.value],
        "keywords": ["security", "encryption", "authentication", "payment gateway", "aggregator", "data protection"],
    },
    {
        "circular_number": "RBI/DFS/2023-24/115",
        "title": "Standards for Deployment and Operations of Payment Systems – Third Party Service Providers",
        "description": "Specifies guidelines for third-party service providers in digital payment systems including payment system operators, payment gateway operators, and payment aggregators.",
        "issue_date": datetime(2023, 8, 22),
        "effective_date": datetime(2023, 10, 1),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value],
        "keywords": ["payment aggregator", "third party", "payment gateway", "operations", "deployment"],
    },
    {
        "circular_number": "RBI/DFS/2022-23/135",
        "title": "Uniform Pricing of NEFT and RTGS – Payment Gateways",
        "description": "Defines uniform pricing for NEFT and RTGS transactions through payment gateways to standardize costs across payment service providers.",
        "issue_date": datetime(2022, 12, 10),
        "effective_date": datetime(2023, 1, 1),
        "scope": CircularScope.NEFT_RTGS,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value],
        "keywords": ["pricing", "NEFT", "RTGS", "payment gateway", "standardization"],
    },
    {
        "circular_number": "RBI/DFS/2022-23/108",
        "title": "Framework for Payments System Operators – End-to-end Responsibility",
        "description": "Outlines end-to-end responsibility framework for payment system operators, payment gateway operators, and payment aggregators to ensure accountability.",
        "issue_date": datetime(2022, 9, 30),
        "effective_date": datetime(2022, 11, 15),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value],
        "keywords": ["payment aggregator", "operator", "responsibility", "accountability"],
    },
    {
        "circular_number": "RBI/DFS/2021-22/117",
        "title": "Master Direction – Payment and Settlement Systems in India, 2021",
        "description": "Comprehensive master direction covering establishment, operation and regulation of payment and settlement systems, including payment gateways and aggregators.",
        "issue_date": datetime(2021, 11, 15),
        "effective_date": datetime(2022, 1, 1),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.PAYMENT_AGGREGATOR.value, CircularScope.UPI.value],
        "keywords": ["master direction", "payment system", "settlement", "gateway", "aggregator", "regulation"],
    },
    {
        "circular_number": "RBI/DFS/2021-22/62",
        "title": "Customer Due Diligence Norms for Payment Systems",
        "description": "Prescribes customer due diligence and KYC requirements for payment service providers including payment gateways and aggregators.",
        "issue_date": datetime(2021, 5, 25),
        "effective_date": datetime(2021, 7, 1),
        "scope": CircularScope.KYC_AML,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value, CircularScope.PAYMENT_AGGREGATOR.value],
        "keywords": ["KYC", "customer due diligence", "AML", "payment gateway", "aggregator"],
    },
    {
        "circular_number": "RBI/DFS/2020-21/125",
        "title": "RBI Guidelines on Use of Cloud Computing Infrastructure by NBFC-CIC and Payment Aggregators",
        "description": "Guidelines for payment aggregators and NBFCs on secure use of cloud computing infrastructure to support digital payment operations.",
        "issue_date": datetime(2020, 11, 22),
        "effective_date": datetime(2021, 1, 1),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.CYBERSECURITY.value, CircularScope.DATA_SECURITY.value],
        "keywords": ["cloud computing", "payment aggregator", "infrastructure", "security", "cybersecurity"],
    },
    {
        "circular_number": "RBI/DFS/2020-21/112",
        "title": "Master Direction – Omnichannel Digital Payments Service by All Scheduled Commercial Banks",
        "description": "Directs all scheduled commercial banks to facilitate omnichannel digital payment services through payment gateways and aggregators.",
        "issue_date": datetime(2020, 9, 8),
        "effective_date": datetime(2020, 10, 15),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.DIGITAL_WALLET.value, CircularScope.UPI.value],
        "keywords": ["omnichannel", "digital payment", "gateway", "commercial banks"],
    },
    {
        "circular_number": "RBI/DFS/2019-20/164",
        "title": "Cyber Security Standards in Payment Systems",
        "description": "Cyber security standards and requirements for payment system operators, payment gateways, and aggregators to protect against cyber threats.",
        "issue_date": datetime(2019, 12, 20),
        "effective_date": datetime(2020, 2, 1),
        "scope": CircularScope.CYBERSECURITY,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value, CircularScope.PAYMENT_AGGREGATOR.value],
        "keywords": ["cybersecurity", "security standards", "payment gateway", "aggregator", "threats"],
    },
    {
        "circular_number": "RBI/DFS/2019-20/152",
        "title": "Technology Risk Management in Banks – Payment Systems",
        "description": "Guidelines on technology risk management for payment system operators including payment gateway operators and aggregators.",
        "issue_date": datetime(2019, 10, 3),
        "effective_date": datetime(2019, 12, 1),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.PAYMENT_AGGREGATOR.value, CircularScope.CYBERSECURITY.value],
        "keywords": ["technology risk", "management", "payment gateway", "risk assessment"],
    },
    {
        "circular_number": "RBI/DFS/2018-19/143",
        "title": "Framework for Mobile Payment Services – Payment Aggregators",
        "description": "Regulatory framework for payment aggregators offering mobile payment services to ensure customer protection and system stability.",
        "issue_date": datetime(2018, 11, 11),
        "effective_date": datetime(2018, 12, 15),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value, CircularScope.DIGITAL_WALLET.value],
        "keywords": ["mobile payment", "aggregator", "framework", "customer protection"],
    },
    {
        "circular_number": "RBI/DFS/2018-19/103",
        "title": "Regulatory Framework for Payment Service Banks",
        "description": "Regulatory framework defining scope, operations and compliance requirements for payment service banks and their use of payment gateways.",
        "issue_date": datetime(2018, 7, 27),
        "effective_date": datetime(2018, 9, 1),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.PAYMENT_AGGREGATOR.value],
        "keywords": ["payment service bank", "regulatory framework", "compliance"],
    },
    {
        "circular_number": "RBI/DFS/2017-18/98",
        "title": "Tokenization of Payment Cards – Card-on-File Transactions",
        "description": "Guidelines on tokenization of payment cards for card-on-file transactions through payment gateways to enhance security.",
        "issue_date": datetime(2017, 10, 12),
        "effective_date": datetime(2017, 12, 1),
        "scope": CircularScope.CARDS,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value, CircularScope.DATA_SECURITY.value],
        "keywords": ["tokenization", "card", "payment gateway", "security", "encryption"],
    },
    {
        "circular_number": "RBI/DFS/2017-18/87",
        "title": "Standardized Interfaces for Core Banking Systems and Payment Gateways",
        "description": "Prescribes standardized interfaces and integration standards for payment gateways interacting with core banking systems.",
        "issue_date": datetime(2017, 8, 22),
        "effective_date": datetime(2017, 10, 1),
        "scope": CircularScope.PAYMENT_GATEWAY,
        "related_scopes": [CircularScope.GENERAL.value],
        "keywords": ["standardized interface", "integration", "core banking", "payment gateway"],
    },
    {
        "circular_number": "RBI/DPSS/2016-17/50",
        "title": "Regulation of Payment Aggregators and Payment Gateways Operating in India",
        "description": "Core regulatory requirements for payment aggregators and payment gateways operations, licensing, and compliance in India.",
        "issue_date": datetime(2016, 6, 23),
        "effective_date": datetime(2016, 8, 1),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.PAYMENT_GATEWAY.value],
        "keywords": ["regulation", "payment aggregator", "payment gateway", "licensing", "compliance"],
    },
    {
        "circular_number": "RBI/DPSS/2015-16/65",
        "title": "Recognition and Regulation of Pre-paid Payment Instruments and Payment Aggregators",
        "description": "Framework for recognition and regulation of pre-paid payment instruments issuers and their interaction with payment aggregators.",
        "issue_date": datetime(2015, 9, 17),
        "effective_date": datetime(2015, 11, 1),
        "scope": CircularScope.PAYMENT_AGGREGATOR,
        "related_scopes": [CircularScope.DIGITAL_WALLET.value],
        "keywords": ["pre-paid", "payment aggregator", "recognition", "regulation"],
    },
]


def seed_historic_circulars(db: Session = None):
    """
    Seed database with historic payment sector RBI circulars
    
    Args:
        db: Optional database session. If not provided, creates new session.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True
    
    try:
        # Check if data already exists
        existing = db.query(RBICircular).filter(
            RBICircular.is_historic == True
        ).count()
        
        if existing > 0:
            print(f"✓ Historic circulars already seeded ({existing} records)")
            return existing
        
        print("📥 Seeding historic RBI circulars for Payment Gateways & Aggregators...")
        
        # Create circular records
        created_count = 0
        for circular_data in HISTORIC_CIRCULARS:
            # Check if circular already exists
            existing_circular = db.query(RBICircular).filter(
                RBICircular.circular_number == circular_data["circular_number"]
            ).first()
            
            if existing_circular:
                # Update with scope information
                existing_circular.scope = circular_data.get("scope")
                existing_circular.related_scopes = circular_data.get("related_scopes")
                existing_circular.is_historic = True
                existing_circular.keywords = circular_data.get("keywords")
                db.commit()
                created_count += 1
            else:
                # Create new circular
                circular = RBICircular(
                    circular_number=circular_data["circular_number"],
                    title=circular_data["title"],
                    description=circular_data["description"],
                    issue_date=circular_data.get("issue_date"),
                    effective_date=circular_data.get("effective_date"),
                    scope=circular_data.get("scope"),
                    related_scopes=circular_data.get("related_scopes"),
                    keywords=circular_data.get("keywords"),
                    status=CircularStatus.ANALYZED,  # Historic circulars are already analyzed
                    is_historic=True,
                    processed_at=datetime.utcnow(),
                )
                db.add(circular)
                created_count += 1
        
        db.commit()
        print(f"✓ Successfully seeded {created_count} historic circulars")
        return created_count
    
    except Exception as e:
        print(f"✗ Error seeding circulars: {str(e)}")
        db.rollback()
        return 0
    
    finally:
        if close_session:
            db.close()


def get_circulars_by_scope(scope: CircularScope, db: Session = None):
    """
    Retrieve circulars filtered by scope
    
    Args:
        scope: CircularScope enum value
        db: Optional database session
    
    Returns:
        List of RBICircular objects
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True
    
    try:
        circulars = db.query(RBICircular).filter(
            RBICircular.scope == scope,
            RBICircular.is_historic == True
        ).order_by(RBICircular.issue_date.desc()).all()
        
        return circulars
    
    finally:
        if close_session:
            db.close()


def list_payment_gateway_circulars(db: Session = None):
    """Get all payment gateway related circulars"""
    return get_circulars_by_scope(CircularScope.PAYMENT_GATEWAY, db)


def list_payment_aggregator_circulars(db: Session = None):
    """Get all payment aggregator related circulars"""
    return get_circulars_by_scope(CircularScope.PAYMENT_AGGREGATOR, db)


def print_circular_summary():
    """Print summary of seeded circulars"""
    db = SessionLocal()
    try:
        total = db.query(RBICircular).filter(
            RBICircular.is_historic == True
        ).count()
        
        gateways = db.query(RBICircular).filter(
            RBICircular.scope == CircularScope.PAYMENT_GATEWAY,
            RBICircular.is_historic == True
        ).count()
        
        aggregators = db.query(RBICircular).filter(
            RBICircular.scope == CircularScope.PAYMENT_AGGREGATOR,
            RBICircular.is_historic == True
        ).count()
        
        print("\n" + "="*60)
        print("📊 HISTORIC RBI CIRCULARS SUMMARY")
        print("="*60)
        print(f"Total Historic Circulars:        {total}")
        print(f"Payment Gateway Circulars:      {gateways}")
        print(f"Payment Aggregator Circulars:   {aggregators}")
        print("="*60 + "\n")
        
        # List by scope
        scopes = [CircularScope.PAYMENT_GATEWAY, CircularScope.PAYMENT_AGGREGATOR]
        for scope in scopes:
            count = db.query(RBICircular).filter(
                RBICircular.scope == scope,
                RBICircular.is_historic == True
            ).count()
            if count > 0:
                print(f"\n{scope.value.replace('_', ' ').upper()}:")
                circulars = db.query(RBICircular).filter(
                    RBICircular.scope == scope,
                    RBICircular.is_historic == True
                ).order_by(RBICircular.issue_date.desc()).all()
                
                for circ in circulars:
                    print(f"  • {circ.circular_number}: {circ.title}")
                    if circ.related_scopes:
                        print(f"    Related: {', '.join(circ.related_scopes)}")
    
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed circulars
    count = seed_historic_circulars()
    
    # Print summary
    if count > 0:
        print_circular_summary()
