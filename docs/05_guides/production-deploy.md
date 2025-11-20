# Production Deployment Guide

> **Status**: 🚧 Documentation in Progress

## Overview

Complete guide for deploying SpecQL-generated backends to production.

## Coming Soon

- Database setup and migrations
- Environment configuration
- CI/CD integration
- Monitoring and alerts
- Backup and recovery

## Quick Start

```bash
# Run migrations
psql production < db/schema/*.sql

# Set environment
export DATABASE_URL="postgresql://..."
export NODE_ENV="production"
```

## Related

- [Deployment](../07_advanced/deployment.md)
- [Infrastructure](../04_infrastructure/index.md)
- [Security](../07_advanced/security-hardening.md)

---

*Last Updated*: 2025-11-20
