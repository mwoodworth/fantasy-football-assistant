#!/usr/bin/env python3
"""
Comprehensive database check and fix script.
Ensures all tables have the required columns based on the SQLAlchemy models.
"""

import sys
from pathlib import Path
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.database import engine, Base
from src.models import *  # Import all models to ensure they're registered

def check_and_fix_database():
    """Check and fix all database tables"""
    
    inspector = inspect(engine)
    
    # Get all table names from the database
    existing_tables = inspector.get_table_names()
    print(f"Existing tables in database: {existing_tables}")
    
    # Get all tables defined in models
    model_tables = Base.metadata.tables.keys()
    print(f"\nTables defined in models: {list(model_tables)}")
    
    # Create any missing tables
    missing_tables = set(model_tables) - set(existing_tables)
    if missing_tables:
        print(f"\n⚠️  Missing tables: {missing_tables}")
        print("Creating missing tables...")
        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[t] for t in missing_tables])
        print("✅ Missing tables created!")
    else:
        print("\n✅ All model tables exist in database")
    
    # Check for missing columns in existing tables
    print("\n🔍 Checking for missing columns...")
    
    with engine.connect() as conn:
        for table_name in existing_tables:
            if table_name in Base.metadata.tables:
                model_table = Base.metadata.tables[table_name]
                
                # Get existing columns from database
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                existing_columns = {row[1] for row in result}
                
                # Get expected columns from model
                expected_columns = {col.name for col in model_table.columns}
                
                # Find missing columns
                missing_columns = expected_columns - existing_columns
                
                if missing_columns:
                    print(f"\n⚠️  Table '{table_name}' is missing columns: {missing_columns}")
                    
                    # Add missing columns
                    for col_name in missing_columns:
                        col = model_table.columns[col_name]
                        col_type = str(col.type)
                        
                        # Determine default value
                        if col.nullable:
                            default_value = "NULL"
                        elif col.default:
                            if callable(col.default.arg):
                                default_value = "NULL"  # Can't set function defaults in ALTER TABLE
                            else:
                                default_value = f"'{col.default.arg}'"
                        elif str(col.type) == "BOOLEAN":
                            default_value = "0"
                        elif "INTEGER" in str(col.type).upper():
                            default_value = "0"
                        elif "FLOAT" in str(col.type).upper():
                            default_value = "0.0"
                        else:
                            default_value = "''"
                        
                        try:
                            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
                            conn.execute(text(alter_sql))
                            conn.commit()
                            print(f"  ✅ Added column: {col_name}")
                        except Exception as e:
                            print(f"  ❌ Error adding column {col_name}: {e}")
                else:
                    print(f"✅ Table '{table_name}' has all required columns")
    
    print("\n🎉 Database check and fix complete!")

if __name__ == "__main__":
    check_and_fix_database()