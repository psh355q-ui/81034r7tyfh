# DB Schema Manager - Migration Guide

**Last Updated**: 2025-12-25  
**Version**: 1.0.0

---

## 📋 Overview

This guide explains how to create, update, and manage database schemas using the DB Schema Manager.

---

## 🎯 Quick Start

### 1. Get the full SQL migration
```bash
cd d:\code\ai-trading-system
python backend/ai/skills/system/db-schema-manager/scripts/generate_migration.py dividend_aristocrats
```

### 2. Compare schema with actual DB
```bash
python backend/ai/skills/system/db-schema-manager/scripts/compare_to_db.py dividend_aristocrats
```

### 3. Validate data before insert
```bash
python backend/ai/skills/system/db-schema-manager/scripts/validate_data.py dividend_aristocrats '{"ticker": "JNJ", ...}'
```

---

## 🏗️ Creating a New Table

### Step 1: Define Schema (JSON)

Create `schemas/your_table.json`:

```json
{
  "table_name": "your_table",
  "description": "Brief description of the table purpose",
  "primary_key": "id",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "description": "Primary key"
    },
    {
      "name": "ticker",
      "type": "VARCHAR(10)",
      "nullable": false,
      "description": "Stock ticker symbol"
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "nullable": false,
      "default": "CURRENT_TIMESTAMP",
      "description": "Record creation timestamp"
    }
  ],
  "indexes": [
    {
      "name": "idx_your_table_ticker",
      "columns": ["ticker"],
      "unique": false
    }
  ],
  "metadata": {
    "phase": "Phase XX",
    "created": "2025-12-25",
    "related_files": [
      "backend/api/your_router.py",
      "backend/database/models.py"
    ]
  }
}
```

### Step 2: Generate SQL

```bash
python scripts/generate_migration.py your_table --output-file migrations/create_your_table.sql
```

### Step 3: Execute SQL

```bash
psql -h localhost -U postgres -d ai_trading -f migrations/create_your_table.sql
```

OR run Python migration:
```bash
python simple_migrate.py  # If migration script exists
```

### Step 4: Verify

```bash
python scripts/compare_to_db.py your_table
```

---

## 🔄 Updating Existing Table

### Scenario: Add New Column

1. **Update JSON schema**:
   ```json
   {
     "name": "new_column",
     "type": "VARCHAR(50)",
     "nullable": true,
     "description": "New feature column"
   }
   ```

2. **Generate ALTER TABLE SQL**:
   ```bash
   python scripts/generate_migration.py your_table
   ```
   
   Extract the `ALTER TABLE` statement (manual for now).

3. **Apply change**:
   ```sql
   ALTER TABLE your_table ADD COLUMN new_column VARCHAR(50);
   ```

4. **Verify**:
   ```bash
   python scripts/compare_to_db.py your_table
   ```

---

## 📊 Schema Comparison

### Check Single Table

```bash
python scripts/compare_to_db.py dividend_aristocrats
```

**Output** (if mismatch):
```
❌ dividend_aristocrats: Schema mismatch!
  ❌ Missing columns in DB: ['payout_ratio', 'market_cap']
  ⚠️  Extra columns in DB (not in schema): ['old_field']
  ❌ Type mismatch for 'sector': defined=VARCHAR(50), actual=TEXT
```

### Check All Tables

```bash
python scripts/compare_to_db.py --all
```

**Output**:
```
✅ dividend_aristocrats: Schema matches!
❌ news_articles: Schema mismatch!
  ...
✅ trading_signals: Schema matches!

📊 Summary: 35/40 tables match
```

---

## ✅ Data Validation

### Before Database Insert

```python
import subprocess
import json

data = {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "consecutive_years": 11,
    "is_sp500": 1,
    "is_reit": 0,
    "created_at": "2025-12-25T00:00:00",
    "updated_at": "2025-12-25T00:00:00"
}

# Validate
result = subprocess.run(
    ["python", "scripts/validate_data.py", "dividend_aristocrats", json.dumps(data)],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Valid - proceed to insert")
    # db.insert(dividend_aristocrats).values(**data).execute()
else:
    print(f"❌ Invalid:\n{result.stdout}")
```

---

## 🗂️ Schema File Format

### Required Fields

```json
{
  "table_name": "string (required)",
  "description": "string (required)",
  "primary_key": "string or array (required)",
  "columns": [ ... ] (required, at least 1),
  "indexes": [ ... ] (optional),
  "metadata": { ... } (optional)
}
```

### Column Definition

```json
{
  "name": "column_name (required)",
  "type": "SQL_TYPE (required, e.g., VARCHAR(10), INTEGER)",
  "nullable": true/false (optional, default: true),
  "default": "value or CURRENT_TIMESTAMP (optional)",
  "description": "Human-readable description (optional)",
  "example": "Example value for documentation (optional)"
}
```

### Index Definition

```json
{
  "name": "idx_table_column (required)",
  "columns": ["col1", "col2"] (required),
  "unique": true/false (optional, default: false),
  "order": "ASC or DESC (optional, default: ASC)",
  "description": "Index purpose (optional)"
}
```

---

## 🛠️ Common Tasks

### Task 1: Fix Schema Mismatch

**Problem**: `compare_to_db.py` reports mismatch

**Solution**:
1. Identify which is correct: JSON schema or DB
2. If JSON is correct:
   ```bash
   python scripts/generate_migration.py table_name
   # Apply ALTER TABLE from output
   ```
3. If DB is correct:
   ```bash
   # Update schemas/table_name.json manually
   python scripts/compare_to_db.py table_name  # Verify
   ```

### Task 2: Add Table to Existing System

1. Define schema JSON
2. Generate migration SQL
3. Apply to database
4. Update SQLAlchemy model in `backend/database/models.py`
5. Add to imports in `backend/database/__init__.py`

### Task 3: Bulk Schema Export

```bash
# Export all current DB schemas to JSON (future script)
python scripts/export_db_to_json.py  # TODO: Not yet implemented
```

---

## 🚨 Troubleshooting

### Error: "Schema not found"

```
❌ Schema not found: .../schemas/table_name.json
```

**Solution**: Create `schemas/table_name.json` first.

### Error: "DATABASE_URL not found"

```
❌ DATABASE_URL not found in environment or .env file
```

**Solution**: 
1. Create `.env` file in project root
2. Add: `DATABASE_URL="postgresql://user:pass@localhost/ai_trading"`

### Error: "psycopg2 not installed"

```
❌ psycopg2 not installed.
```

**Solution**:
```bash
pip install psycopg2-binary
```

### Validation Error: "Field required"

```
❌ Validation failed for table 'dividend_aristocrats':
  • created_at: Field required
```

**Solution**: Add missing required fields to your data.

---

## 📈 Best Practices

### 1. Always Validate Before Insert

```python
# Good
validate_data(table, data)
if valid:
    db.insert(data)

# Bad
db.insert(data)  # May fail silently or corrupt data
```

### 2. Keep Schemas In Sync

- JSON schema = Source of Truth
- Update JSON first, then DB
- Run `compare_to_db.py` regularly

### 3. Document Changes

Add to `metadata.notes`:
```json
{
  "metadata": {
    "notes": "2025-12-25: Added market_cap column for valuation"
  }
}
```

### 4. Use Descriptive Names

**Good**: 
- `idx_aristocrat_consecutive_years`
- `dividend_growth_5y`

**Bad**:
- `idx1`
- `col_a`

---

## 🔮 Roadmap

### Phase 2 ✅
- [x] `compare_to_db.py` - Compare schemas
- [x] `generate_migration.py` - Generate SQL
- [ ] Documentation complete

### Phase 3
- [ ] Add remaining 35+ table schemas
- [ ] `validate_schema.py` - Validate JSON itself
- [ ] `export_db_to_json.py` - Auto-generate from existing DB

### Phase 4
- [ ] Auto-migration tool (apply ALTER TABLE automatically)
- [ ] Schema versioning
- [ ] Rollback support

---

**Questions?** Check `SKILL.md` or `SCHEMA_REFERENCE.md`
