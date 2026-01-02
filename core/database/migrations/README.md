# Database Migrations

This directory contains database schema migrations for AAS.

## Migration System

AAS uses **Alembic** for database migrations, providing:
- Version control for database schema
- Automatic migration generation from model changes
- Rollback support for safe schema updates

## Setup

Install Alembic (already in requirements.txt):
```bash
pip install alembic
```

Initialize Alembic (first time only):
```bash
alembic init core/database/migrations
```

## Usage

### Generate Migration from Model Changes
```bash
# After modifying models.py
alembic revision --autogenerate -m "Add user table"
```

### Apply Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision>
```

### Rollback Migrations
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

### View Migration History
```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Workflow

1. **Modify Models**: Edit `core/database/models.py`
2. **Generate Migration**: `alembic revision --autogenerate -m "Description"`
3. **Review**: Check generated migration in `versions/`
4. **Apply**: `alembic upgrade head`
5. **Test**: Verify schema changes work correctly
6. **Commit**: Commit both model and migration files

## Best Practices

- **Review Auto-Generated Migrations**: Alembic may not catch all changes
- **Add Data Migrations**: Include data transformations if needed
- **Test Rollbacks**: Ensure `downgrade()` works correctly
- **One Logical Change Per Migration**: Keep migrations focused
- **Never Edit Applied Migrations**: Create new migrations instead

## Schema Version Tracking

Alembic stores the current schema version in the `alembic_version` table.
This ensures migrations are applied in order and never duplicated.

## Initial Schema

The initial schema includes:
- **tasks**: Task tracking (synced with ACTIVE_TASKS.md)
- **task_executions**: Execution history by agents
- **events**: Health monitoring events
- **plugins**: Plugin registry and state
- **config_entries**: Runtime configuration storage

See `models.py` for complete schema definitions.
