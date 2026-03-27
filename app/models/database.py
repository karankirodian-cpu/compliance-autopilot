from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class CircularStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Priority(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ActionStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class ProductCategory(enum.Enum):
    DIGITAL_PAYMENTS = "digital_payments"
    LENDING = "lending"
    DEPOSITS = "deposits"
    WEALTH_MANAGEMENT = "wealth_management"
    INSURANCE = "insurance"
    CARDS = "cards"
    CORE_BANKING = "core_banking"
    KYC_AML = "kyc_aml"
    RISK_MANAGEMENT = "risk_management"
    ALL = "all"

class CircularScope(enum.Enum):
    PAYMENT_GATEWAY = "payment_gateway"
    PAYMENT_AGGREGATOR = "payment_aggregator"
    DIGITAL_WALLET = "digital_wallet"
    UPI = "upi"
    NEFT_RTGS = "neft_rtgs"
    FOREX = "forex"
    LENDING = "lending"
    DEPOSITS = "deposits"
    CARDS = "cards"
    KYC_AML = "kyc_aml"
    CYBERSECURITY = "cybersecurity"
    DATA_SECURITY = "data_security"
    GENERAL = "general"

class RBICircular(Base):
    __tablename__ = "rbi_circulars"
    
    id = Column(Integer, primary_key=True)
    circular_number = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    issue_date = Column(DateTime)
    effective_date = Column(DateTime)
    document_url = Column(String)
    document_path = Column(String)
    status = Column(Enum(CircularStatus), default=CircularStatus.PENDING)
    raw_content = Column(Text)
    extracted_entities = Column(JSON)  # {entities: [], regulations: [], penalties: []}
    keywords = Column(JSON)
    scope = Column(Enum(CircularScope), nullable=True, index=True)  # Primary scope
    related_scopes = Column(JSON)  # List of related scopes
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    is_historic = Column(Boolean, default=False, index=True)  # Mark as historic data
    
    impact_assessments = relationship("ImpactAssessment", back_populates="circular")
    action_items = relationship("ActionItem", back_populates="circular")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    description = Column(Text)
    owner_team = Column(String)
    compliance_contacts = Column(JSON)  # [email1, email2]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    impact_assessments = relationship("ImpactAssessment", back_populates="product")

class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"
    
    id = Column(Integer, primary_key=True)
    circular_id = Column(Integer, ForeignKey("rbi_circulars.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    impact_level = Column(Enum(Priority), nullable=False)
    affected_areas = Column(JSON)  # List of affected system areas
    compliance_requirements = Column(JSON)  # Extracted requirements
    deadline = Column(DateTime)
    notes = Column(Text)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    assessed_by = Column(String)
    
    circular = relationship("RBICircular", back_populates="impact_assessments")
    product = relationship("Product", back_populates="impact_assessments")

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True)
    circular_id = Column(Integer, ForeignKey("rbi_circulars.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    assigned_to = Column(String, nullable=False)  # Email or team
    status = Column(Enum(ActionStatus), default=ActionStatus.PENDING)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reminder_sent = Column(Boolean, default=False)
    
    circular = relationship("RBICircular", back_populates="action_items")

class ComplianceTracker(Base):
    __tablename__ = "compliance_tracker"
    
    id = Column(Integer, primary_key=True)
    circular_id = Column(Integer, ForeignKey("rbi_circulars.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    implementation_status = Column(String)  # Not Started, In Progress, Completed
    evidence_document = Column(String)
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    comments = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    product_categories = Column(JSON)  # List of categories to monitor
    keywords = Column(JSON)  # Trigger keywords
    priority_threshold = Column(Enum(Priority), default=Priority.MEDIUM)
    notify_emails = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    entity_type = Column(String)  # Circular, ActionItem, etc.
    entity_id = Column(Integer)
    user = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database connection
engine = create_engine("sqlite:///compliance_autopilot.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()