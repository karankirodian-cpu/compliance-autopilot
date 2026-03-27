#!/usr/bin/env python
"""
Management CLI for Compliance Autopilot database operations
Run: python manage.py --help
"""
import argparse
import sys
from app.models.database import Base, engine, SessionLocal, CircularScope
from app.scripts.seed_historic_circulars import (
    seed_historic_circulars,
    print_circular_summary,
    list_payment_gateway_circulars,
    list_payment_aggregator_circulars,
)


def init_db():
    """Initialize database with all tables"""
    print("🔨 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def seed_data():
    """Seed historic circulars"""
    print("📥 Seeding historic circulars...")
    count = seed_historic_circulars()
    print(f"✓ Created/Updated {count} historic circulars")


def list_gateway_circulars():
    """List all payment gateway circulars"""
    print("\n📋 PAYMENT GATEWAY CIRCULARS:")
    print("="*70)
    circulars = list_payment_gateway_circulars()
    if not circulars:
        print("No Payment Gateway circulars found")
    else:
        for c in circulars:
            print(f"  • {c.circular_number}: {c.title}")
            print(f"    Issue: {c.issue_date.strftime('%d %b %Y') if c.issue_date else 'N/A'}")
            if c.related_scopes:
                print(f"    Related: {', '.join(c.related_scopes)}\n")


def list_aggregator_circulars():
    """List all payment aggregator circulars"""
    print("\n📋 PAYMENT AGGREGATOR CIRCULARS:")
    print("="*70)
    circulars = list_payment_aggregator_circulars()
    if not circulars:
        print("No Payment Aggregator circulars found")
    else:
        for c in circulars:
            print(f"  • {c.circular_number}: {c.title}")
            print(f"    Issue: {c.issue_date.strftime('%d %b %Y') if c.issue_date else 'N/A'}")
            if c.related_scopes:
                print(f"    Related: {', '.join(c.related_scopes)}\n")


def show_stats():
    """Show database statistics"""
    print("\n📊 DATABASE STATISTICS:")
    print("="*70)
    print_circular_summary()


def reset_db():
    """⚠️  DANGEROUS: Reset entire database"""
    confirm = input("⚠️  WARNING: This will DELETE all data. Type 'yes' to confirm: ")
    if confirm.lower() == "yes":
        print("🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("🔨 Recreating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database reset complete")
    else:
        print("✗ Reset cancelled")


def main():
    parser = argparse.ArgumentParser(
        description="Compliance Autopilot - Database Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage.py init           # Initialize database
  python manage.py seed           # Seed historic circulars
  python manage.py stats          # Show database statistics
  python manage.py list-gateway   # List Payment Gateway circulars
  python manage.py list-aggregator # List Payment Aggregator circulars
  python manage.py reset          # DANGEROUS: Reset database
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    commands = {
        "init": init_db,
        "seed": seed_data,
        "stats": show_stats,
        "list-gateway": list_gateway_circulars,
        "list-aggregator": list_aggregator_circulars,
        "reset": reset_db,
    }
    
    if not args.command or args.command == "help":
        parser.print_help()
        return
    
    if args.command not in commands:
        print(f"✗ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)
    
    try:
        commands[args.command]()
    except Exception as e:
        print(f"✗ Error executing command: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
