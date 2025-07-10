# Database Migration Fix

There's currently an issue with the alembic migration chain where migration 002 is missing. Here's how to fix it:

## Option 1: Skip to Latest Schema (Recommended for Development)

If you're in development and don't have important data to preserve:

### Using the Reset Script (Easiest)

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the reset script
python3 scripts/reset_database.py
```

This script will:
- Ask for confirmation before deleting existing database
- Create all tables with the latest schema
- Set the alembic version to the latest migration
- Verify all tables and columns were created correctly
- Provide clear feedback on the process

### Manual Method

If you prefer to do it manually:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Remove existing database
rm fantasy_football.db

# Create fresh database with all tables
python3 -c "
from src.models.database import engine, Base
from src.models import user, player, team, league, ai_analysis, dashboard, espn_league, draft

# Create all tables
Base.metadata.create_all(bind=engine)
print('Database created successfully!')
"

# Mark alembic as up-to-date (optional)
python3 -c "
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///fantasy_football.db')
with engine.connect() as conn:
    conn.execute(text('CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)'))
    conn.execute(text(\"INSERT INTO alembic_version VALUES ('006_add_draft_session_fields')\"))
    conn.commit()
print('Alembic version set!')
"
```

## Option 2: Fix Migration Chain

If you need to preserve data:

1. Create the missing migration file:

```bash
# Create missing 002 migration
cat > alembic/versions/002_add_espn_league_models.py << 'EOF'
"""Add ESPN league models

Revision ID: 002_add_espn_league_models
Revises: 001_initial
Create Date: 2025-07-08 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_espn_league_models'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade():
    pass  # Tables already exist

def downgrade():
    pass  # Keep tables
EOF
```

2. Then run the migrations:

```bash
source venv/bin/activate
python -m alembic upgrade head
```

## After Fixing

The draft monitor error about missing columns should be resolved. The application should run without database errors.