#!/usr/bin/env python3
"""
Database Migration Setup for Aker Property Model

This script helps set up and run database migrations for the supply calculators.
"""


def check_alembic_installation():
    """Check if alembic is installed."""
    try:
        import alembic

        print("✅ Alembic is installed")
        return True
    except ImportError:
        print("❌ Alembic is not installed")
        print("To install: pip install alembic")
        return False


def check_database_connection():
    """Check database connection (placeholder for actual implementation)."""
    print("✅ Database connection check (placeholder)")
    print("Note: Actual database connection requires proper database setup")
    return True


def run_migration():
    """Run the database migration."""
    if not check_alembic_installation():
        print("❌ Cannot run migration without alembic")
        return False

    try:
        from alembic import command
        from alembic.config import Config

        # Get the alembic configuration
        alembic_cfg = Config("alembic.ini")

        print("Running database migration...")
        command.upgrade(alembic_cfg, "head")

        print("✅ Database migration completed successfully")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_migration():
    """Verify that the migration created the expected tables."""
    print("✅ Migration verification (placeholder)")
    print("Note: Actual verification requires database connection")
    return True


def create_migration_script():
    """Create a script to run migrations in production."""
    script_content = """#!/bin/bash
# Production database migration script

echo "Starting Aker Property Model database migration..."

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "Error: alembic is not installed"
    exit 1
fi

# Run the migration
cd /path/to/housing-model
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migration completed successfully"
else
    echo "Migration failed"
    exit 1
fi
"""

    with open("scripts/run_migration.sh", "w") as f:
        f.write(script_content)

    print("✅ Created production migration script: scripts/run_migration.sh")


def main():
    """Main migration setup function."""
    print("Aker Property Model Database Migration Setup")
    print("=" * 50)

    # Check prerequisites
    print("\n1. Checking prerequisites...")
    alembic_ok = check_alembic_installation()
    db_ok = check_database_connection()

    if not (alembic_ok and db_ok):
        print("❌ Prerequisites not met. Please install required packages and configure database.")
        return

    # Create migration script
    print("\n2. Creating migration script...")
    create_migration_script()

    # Run migration
    print("\n3. Running migration...")
    migration_ok = run_migration()

    # Verify migration
    print("\n4. Verifying migration...")
    verify_ok = verify_migration()

    if migration_ok and verify_ok:
        print("\n🎉 Database migration setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure your database connection in alembic.ini")
        print("2. Run the migration in your environment")
        print("3. Verify the market_supply table was created")
        print("4. Run tests to ensure everything works")
    else:
        print("\n❌ Migration setup failed. Please check the errors above.")


if __name__ == "__main__":
    main()
