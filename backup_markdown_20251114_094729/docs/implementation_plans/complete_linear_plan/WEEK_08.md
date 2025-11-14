# Week 08: Production Migration & Cutover

**Objective**: Execute production migration with zero data loss

## Pre-Migration Checklist

- [ ] Production backup completed
- [ ] Rollback plan tested
- [ ] Downtime window scheduled (4 hours)
- [ ] Team on standby
- [ ] Monitoring dashboards ready

## Migration Day Timeline

### T-2h: Final Preparation

```bash
# Final production backup
pg_dump printoptim_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Final schema build test
confiture build --env production --dry-run
```

### T-0: Begin Downtime

```bash
# Stop application services
systemctl stop printoptim_api
systemctl stop printoptim_worker

# Make final incremental backup
pg_dump printoptim_production > backup_final_$(date +%Y%m%d_%H%M%S).sql
```

### T+15min: Apply Schema Changes

```bash
# Apply SpecQL-generated schema
psql printoptim_production < db/0_schema/**/*.sql

# Estimated time: 30 minutes
```

### T+45min: Migrate Data

```bash
# Execute data migration
psql printoptim_production < db/migrations/data_migration/001_migrate_printoptim_data.sql

# Estimated time: 60 minutes
```

### T+1h45min: Validate Migration

```bash
# Run validation scripts
psql printoptim_production < db/migrations/validation/001_validate_migration.sql

# Check all validations pass
# Estimated time: 30 minutes
```

### T+2h15min: Smoke Tests

```bash
# Start application in test mode
systemctl start printoptim_api

# Run smoke tests
curl https://api.printoptim.com/health
pytest tests/smoke/ -v

# Estimated time: 15 minutes
```

### T+2h30min: Production Cutover

```bash
# Enable production traffic
# Update DNS / Load balancer
# Monitor error rates
```

### T+4h: Post-Migration Monitoring

- Monitor error logs
- Track performance metrics
- Verify user access
- 24/7 on-call for 48 hours

## Rollback Procedure (if needed)

```bash
# Stop application
systemctl stop printoptim_api
systemctl stop printoptim_worker

# Restore from backup
dropdb printoptim_production
createdb printoptim_production
psql printoptim_production < backup_final_TIMESTAMP.sql

# Restart application
systemctl start printoptim_api
systemctl start printoptim_worker
```

## Deliverables

- ✅ Production migration completed
- ✅ Zero data loss verified
- ✅ Application operational
- ✅ Performance acceptable
- ✅ Post-migration report