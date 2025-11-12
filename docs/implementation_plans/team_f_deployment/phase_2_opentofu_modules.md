# Team F Phase 2: OpenTofu Modules Implementation Plan

**Created**: 2025-11-12
**Phase**: 2 of 5
**Status**: Planning
**Complexity**: High - Infrastructure as Code with cloud providers
**Priority**: HIGH - Enables production cloud deployments
**Prerequisites**: Phase 1 (Docker) complete

---

## Executive Summary

Implement cloud infrastructure generation using **OpenTofu** (open-source Terraform alternative). Generate production-ready AWS infrastructure modules from minimal deployment YAML.

**Goal**: From `deployment.yaml` (20 lines) → Generate OpenTofu modules (2000+ lines)

**Key Deliverables**:
1. OpenTofu module generator architecture
2. AWS infrastructure modules (VPC, RDS, ECS, ALB, CloudWatch)
3. Pattern-based configurations (small-saas, production-saas)
4. Secure-by-default configurations
5. Cost-optimized resource sizing
6. Infrastructure documentation

**Impact**:
- Production AWS deployment without DevOps expertise
- Best practices encoded (security, monitoring, backups)
- Cost-optimized resource selection
- Infrastructure as code with version control

---

## 🎯 Phase 2 Objectives

### Core Goals
1. **OpenTofu Module System**: Modular infrastructure generation
2. **AWS Support**: VPC, RDS, ECS Fargate, ALB, CloudWatch
3. **Pattern-Based Configs**: small-saas and production-saas patterns
4. **Security First**: RLS, encryption, private subnets, security groups
5. **Cost Optimization**: Right-sized instances, backup strategies

### Success Criteria
- ✅ Generate complete AWS infrastructure from deployment.yaml
- ✅ Support small-saas pattern (db.t4g.micro, ECS Fargate)
- ✅ Support production-saas pattern (Multi-AZ, read replicas, autoscaling)
- ✅ All resources follow AWS best practices
- ✅ Generated OpenTofu validates with `tofu validate`
- ✅ Generated infrastructure deploys successfully
- ✅ Cost estimates provided for each pattern

---

## 📋 Technical Design

### Architecture

```
src/generators/deployment/opentofu/
├── __init__.py
├── opentofu_orchestrator.py      # Main OpenTofu generation orchestrator
├── modules/
│   ├── __init__.py
│   ├── networking/
│   │   ├── vpc_generator.py      # VPC, subnets, NAT gateway
│   │   └── security_groups.py    # Security group rules
│   ├── database/
│   │   ├── rds_generator.py      # PostgreSQL RDS with best practices
│   │   └── backup_generator.py   # Backup policies
│   ├── compute/
│   │   ├── ecs_generator.py      # ECS Fargate cluster
│   │   └── task_definition.py    # ECS task definitions
│   ├── loadbalancer/
│   │   └── alb_generator.py      # Application Load Balancer
│   ├── monitoring/
│   │   └── cloudwatch_generator.py  # CloudWatch alarms
│   └── storage/
│       └── s3_generator.py       # S3 buckets for backups/uploads
├── templates/
│   ├── main.tf.j2
│   ├── variables.tf.j2
│   ├── outputs.tf.j2
│   └── modules/
│       ├── networking/
│       ├── database/
│       ├── compute/
│       └── monitoring/
└── patterns/
    ├── small_saas.py             # Pattern: small-saas config
    └── production_saas.py        # Pattern: production-saas config
```

### Deployment YAML Extension

```yaml
# deployment.yaml (EXTENDED for Phase 2)
deployment:
  name: my-app
  framework: fraiseql
  pattern: small-saas

# Cloud platform configuration
platform:
  provider: aws
  region: us-east-1
  availability_zones: 2

# Database configuration
database:
  engine: postgresql
  version: "16"
  size: small  # Maps to db.t4g.micro for small-saas
  storage: 100  # GB
  backup:
    frequency: daily
    retention: 30  # days
  multi_az: false  # true for production-saas

# Application configuration
application:
  instances: 2
  memory: 512  # MB
  cpu: 0.5  # vCPU
  autoscale:
    enabled: true
    min: 2
    max: 10
    target_cpu: 70

# Monitoring
monitoring:
  level: standard  # basic | standard | enterprise
  alarms:
    - type: cpu_high
      threshold: 80
      email: ops@example.com
    - type: db_connections
      threshold: 80  # percentage
```

---

## 🏗️ Implementation Details

### 1. OpenTofu Orchestrator

```python
# src/generators/deployment/opentofu/opentofu_orchestrator.py
from pathlib import Path
from typing import Dict, Any
import json

from .modules.networking.vpc_generator import VPCGenerator
from .modules.database.rds_generator import RDSGenerator
from .modules.compute.ecs_generator import ECSGenerator
from .modules.loadbalancer.alb_generator import ALBGenerator
from .modules.monitoring.cloudwatch_generator import CloudWatchGenerator

class OpenTofuOrchestrator:
    """
    Orchestrates OpenTofu infrastructure generation.
    Generates modular, reusable OpenTofu configurations.
    """

    def __init__(
        self,
        deployment_config: Dict[str, Any],
        pattern: str,
        output_dir: Path
    ):
        self.config = deployment_config
        self.pattern = pattern
        self.output_dir = Path(output_dir) / 'infrastructure' / 'opentofu'

        # Load pattern-specific defaults
        self.pattern_config = self._load_pattern(pattern)

        # Initialize module generators
        self.vpc_gen = VPCGenerator(self.config, self.pattern_config)
        self.rds_gen = RDSGenerator(self.config, self.pattern_config)
        self.ecs_gen = ECSGenerator(self.config, self.pattern_config)
        self.alb_gen = ALBGenerator(self.config, self.pattern_config)
        self.cloudwatch_gen = CloudWatchGenerator(self.config, self.pattern_config)

    def generate(self) -> Dict[str, Path]:
        """Generate all OpenTofu configurations"""
        generated_files = {}

        # Create directory structure
        self.output_dir.mkdir(parents=True, exist_ok=True)
        modules_dir = self.output_dir / 'modules'

        # Generate root module files
        generated_files['main'] = self._generate_main()
        generated_files['variables'] = self._generate_variables()
        generated_files['outputs'] = self._generate_outputs()
        generated_files['terraform_tfvars'] = self._generate_tfvars_example()

        # Generate module: networking
        networking_dir = modules_dir / 'networking'
        networking_dir.mkdir(parents=True, exist_ok=True)
        generated_files['vpc_module'] = self.vpc_gen.generate(networking_dir)

        # Generate module: database
        database_dir = modules_dir / 'database'
        database_dir.mkdir(parents=True, exist_ok=True)
        generated_files['rds_module'] = self.rds_gen.generate(database_dir)

        # Generate module: compute
        compute_dir = modules_dir / 'compute'
        compute_dir.mkdir(parents=True, exist_ok=True)
        generated_files['ecs_module'] = self.ecs_gen.generate(compute_dir)

        # Generate module: load balancer
        lb_dir = modules_dir / 'loadbalancer'
        lb_dir.mkdir(parents=True, exist_ok=True)
        generated_files['alb_module'] = self.alb_gen.generate(lb_dir)

        # Generate module: monitoring
        monitoring_dir = modules_dir / 'monitoring'
        monitoring_dir.mkdir(parents=True, exist_ok=True)
        generated_files['cloudwatch_module'] = self.cloudwatch_gen.generate(monitoring_dir)

        # Generate README
        generated_files['readme'] = self._generate_readme()

        # Generate deployment script
        generated_files['deploy_script'] = self._generate_deploy_script()

        return generated_files

    def _generate_main(self) -> Path:
        """Generate main.tf"""
        app_name = self.config['deployment']['name']
        region = self.config['platform']['region']

        main_tf = f"""# ============================================
# AUTO-GENERATED BY SPECQL TEAM F
# Application: {app_name}
# Pattern: {self.pattern}
# Provider: AWS
# ============================================

terraform {{
  required_version = ">= 1.0"

  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}

  # Backend configuration (customize for your needs)
  backend "s3" {{
    bucket = "{app_name}-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "{region}"
    encrypt = true
    # dynamodb_table = "{app_name}-terraform-locks"  # Uncomment for state locking
  }}
}}

provider "aws" {{
  region = var.aws_region

  default_tags {{
    tags = {{
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "SpecQL-OpenTofu"
      Pattern     = "{self.pattern}"
    }}
  }}
}}

# ====================================
# Networking Module
# ====================================
module "networking" {{
  source = "./modules/networking"

  app_name           = var.app_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}}

# ====================================
# Database Module (RDS PostgreSQL)
# ====================================
module "database" {{
  source = "./modules/database"

  app_name               = var.app_name
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  db_instance_class      = var.db_instance_class
  db_allocated_storage   = var.db_allocated_storage
  db_engine_version      = var.db_engine_version
  db_username            = var.db_username
  db_password            = var.db_password
  multi_az               = var.db_multi_az
  backup_retention_days  = var.db_backup_retention
  app_security_group_id  = module.compute.app_security_group_id
}}

# ====================================
# Compute Module (ECS Fargate)
# ====================================
module "compute" {{
  source = "./modules/compute"

  app_name             = var.app_name
  environment          = var.environment
  vpc_id               = module.networking.vpc_id
  private_subnet_ids   = module.networking.private_subnet_ids
  task_cpu             = var.task_cpu
  task_memory          = var.task_memory
  desired_count        = var.desired_count
  container_image      = var.container_image
  database_url         = module.database.connection_url
  alb_target_group_arn = module.loadbalancer.target_group_arn
}}

# ====================================
# Load Balancer Module
# ====================================
module "loadbalancer" {{
  source = "./modules/loadbalancer"

  app_name           = var.app_name
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
}}

# ====================================
# Monitoring Module
# ====================================
module "monitoring" {{
  source = "./modules/monitoring"

  app_name          = var.app_name
  environment       = var.environment
  ecs_cluster_name  = module.compute.ecs_cluster_name
  ecs_service_name  = module.compute.ecs_service_name
  db_instance_id    = module.database.db_instance_id
  alb_arn_suffix    = module.loadbalancer.alb_arn_suffix
  alarm_email       = var.alarm_email
}}
"""

        main_path = self.output_dir / 'main.tf'
        main_path.write_text(main_tf)
        return main_path

    def _generate_variables(self) -> Path:
        """Generate variables.tf"""
        app_name = self.config['deployment']['name']

        # Map pattern to instance sizes
        instance_sizes = self.pattern_config['aws']['instance_sizes']

        variables_tf = f"""# ============================================
# Variables for {app_name}
# Pattern: {self.pattern}
# ============================================

variable "aws_region" {{
  description = "AWS region"
  type        = string
  default     = "{self.config['platform']['region']}"
}}

variable "app_name" {{
  description = "Application name"
  type        = string
  default     = "{app_name}"
}}

variable "environment" {{
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}}

# ====================================
# Networking Variables
# ====================================

variable "vpc_cidr" {{
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}}

variable "availability_zones" {{
  description = "Number of availability zones"
  type        = number
  default     = {self.config['platform'].get('availability_zones', 2)}
}}

# ====================================
# Database Variables
# ====================================

variable "db_instance_class" {{
  description = "RDS instance class"
  type        = string
  default     = "{instance_sizes['database']}"
}}

variable "db_allocated_storage" {{
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = {self.config['database'].get('storage', 100)}
}}

variable "db_engine_version" {{
  description = "PostgreSQL version"
  type        = string
  default     = "{self.config['database'].get('version', '16')}"
}}

variable "db_username" {{
  description = "Database username"
  type        = string
  default     = "app_user"
  sensitive   = true
}}

variable "db_password" {{
  description = "Database password"
  type        = string
  sensitive   = true
}}

variable "db_multi_az" {{
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = {str(self.config['database'].get('multi_az', False)).lower()}
}}

variable "db_backup_retention" {{
  description = "Backup retention period (days)"
  type        = number
  default     = {self.config['database'].get('backup', {}).get('retention', 30)}
}}

# ====================================
# Compute Variables
# ====================================

variable "task_cpu" {{
  description = "Fargate task CPU units"
  type        = number
  default     = {int(self.config['application'].get('cpu', 0.5) * 1024)}
}}

variable "task_memory" {{
  description = "Fargate task memory (MB)"
  type        = number
  default     = {self.config['application'].get('memory', 512)}
}}

variable "desired_count" {{
  description = "Desired number of ECS tasks"
  type        = number
  default     = {self.config['application'].get('instances', 2)}
}}

variable "container_image" {{
  description = "Docker image for application"
  type        = string
  default     = "{app_name}:latest"
}}

# ====================================
# Monitoring Variables
# ====================================

variable "alarm_email" {{
  description = "Email for CloudWatch alarms"
  type        = string
}}
"""

        variables_path = self.output_dir / 'variables.tf'
        variables_path.write_text(variables_tf)
        return variables_path

    def _generate_outputs(self) -> Path:
        """Generate outputs.tf"""
        outputs_tf = """# ============================================
# Outputs
# ============================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "database_endpoint" {
  description = "RDS endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "database_connection_url" {
  description = "Database connection URL"
  value       = module.database.connection_url
  sensitive   = true
}

output "load_balancer_dns" {
  description = "Application Load Balancer DNS name"
  value       = module.loadbalancer.dns_name
}

output "load_balancer_url" {
  description = "Application URL"
  value       = "https://${module.loadbalancer.dns_name}"
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.compute.ecs_cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.compute.ecs_service_name
}

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    vpc_id             = module.networking.vpc_id
    database_endpoint  = module.database.endpoint
    load_balancer_url  = "https://${module.loadbalancer.dns_name}"
    ecs_cluster        = module.compute.ecs_cluster_name
  }
}
"""

        outputs_path = self.output_dir / 'outputs.tf'
        outputs_path.write_text(outputs_tf)
        return outputs_path

    def _generate_tfvars_example(self) -> Path:
        """Generate terraform.tfvars.example"""
        app_name = self.config['deployment']['name']

        tfvars = f"""# ============================================
# Example terraform.tfvars
# Copy to terraform.tfvars and fill in values
# ============================================

app_name    = "{app_name}"
environment = "production"
aws_region  = "{self.config['platform']['region']}"

# Database credentials (use AWS Secrets Manager in production)
db_username = "app_user"
db_password = "CHANGE_ME_IN_PRODUCTION"

# Container image (update after building)
container_image = "{app_name}:v1.0.0"

# Monitoring
alarm_email = "ops@example.com"
"""

        tfvars_path = self.output_dir / 'terraform.tfvars.example'
        tfvars_path.write_text(tfvars)
        return tfvars_path

    def _generate_readme(self) -> Path:
        """Generate infrastructure README"""
        app_name = self.config['deployment']['name']

        readme = f"""# Infrastructure: {app_name}

**Pattern**: {self.pattern}
**Provider**: AWS
**Generated by**: SpecQL Team F

---

## Quick Start

### Prerequisites

1. **Install OpenTofu**:
   ```bash
   # macOS
   brew install opentofu

   # Linux
   wget https://github.com/opentofu/opentofu/releases/download/v1.6.0/tofu_1.6.0_linux_amd64.zip
   unzip tofu_1.6.0_linux_amd64.zip
   sudo mv tofu /usr/local/bin/
   ```

2. **AWS Credentials**:
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export AWS_DEFAULT_REGION="{self.config['platform']['region']}"
   ```

3. **Configure Variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   vim terraform.tfvars  # Fill in your values
   ```

---

## Deployment Steps

### 1. Initialize OpenTofu
```bash
tofu init
```

### 2. Plan Infrastructure
```bash
tofu plan -out=tfplan
```

Review the plan to see what will be created.

### 3. Apply Infrastructure
```bash
tofu apply tfplan
```

This will create:
- VPC with public and private subnets
- PostgreSQL RDS instance
- ECS Fargate cluster
- Application Load Balancer
- CloudWatch alarms

### 4. Get Outputs
```bash
tofu output
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Application Load Balancer (ALB)        │
│  Public Subnets                          │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  ECS Fargate Tasks                       │
│  Private Subnets (AZ1, AZ2)             │
│  - {app_name} Container                  │
│  - Auto-scaling enabled                  │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  RDS PostgreSQL                          │
│  Private Subnets (AZ1, AZ2)             │
│  - Automated backups                     │
│  - Encrypted at rest                     │
└─────────────────────────────────────────┘
```

---

## Cost Estimate ({self.pattern})

{self._generate_cost_estimate()}

---

## Monitoring

CloudWatch alarms configured for:
- High CPU usage (> 80%)
- High memory usage (> 80%)
- Database connection threshold
- ALB target health

Notifications sent to: `{self.config.get('monitoring', {}).get('alarms', [{}])[0].get('email', 'ops@example.com')}`

---

## Updating Infrastructure

After making changes to deployment.yaml:

1. Regenerate OpenTofu configurations:
   ```bash
   specql deploy generate deployment.yaml
   ```

2. Review changes:
   ```bash
   tofu plan
   ```

3. Apply changes:
   ```bash
   tofu apply
   ```

---

## Destroying Infrastructure

**WARNING**: This will destroy all resources!

```bash
tofu destroy
```

---

## Troubleshooting

### State File Issues
```bash
# List state resources
tofu state list

# Show specific resource
tofu state show module.database.aws_db_instance.main
```

### Database Connection
```bash
# Get database endpoint
DB_ENDPOINT=$(tofu output -raw database_endpoint)

# Connect to database
psql -h $DB_ENDPOINT -U app_user -d {app_name}
```

---

## Next Steps

1. Deploy application container to ECR
2. Update ECS task definition with container image
3. Configure domain name in Route53
4. Enable HTTPS with ACM certificate
5. Set up CI/CD pipeline

For more information, see: https://github.com/fraiseql/specql
"""

        readme_path = self.output_dir / 'README.md'
        readme_path.write_text(readme)
        return readme_path

    def _generate_cost_estimate(self) -> str:
        """Generate cost estimate for pattern"""
        if self.pattern == 'small-saas':
            return """
**Estimated Monthly Cost**: ~$50-100/month

- RDS db.t4g.micro: ~$15/month
- ECS Fargate (2 tasks, 0.5 vCPU, 512 MB): ~$30/month
- ALB: ~$20/month
- Data transfer: ~$5-15/month
"""
        elif self.pattern == 'production-saas':
            return """
**Estimated Monthly Cost**: ~$300-500/month

- RDS db.m5.large (Multi-AZ): ~$250/month
- ECS Fargate (5-10 tasks, autoscaling): ~$150-300/month
- ALB: ~$20/month
- CloudWatch, data transfer: ~$30/month
"""
        else:
            return "Cost estimate varies by pattern and usage."

    def _generate_deploy_script(self) -> Path:
        """Generate deployment script"""
        script = """#!/bin/bash
set -e

echo "🚀 Deploying infrastructure..."

# Check prerequisites
command -v tofu >/dev/null 2>&1 || { echo "❌ OpenTofu not installed"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not installed"; exit 1; }

# Check AWS credentials
aws sts get-caller-identity >/dev/null 2>&1 || { echo "❌ AWS credentials not configured"; exit 1; }

# Check terraform.tfvars exists
if [ ! -f terraform.tfvars ]; then
    echo "❌ terraform.tfvars not found. Copy terraform.tfvars.example and configure."
    exit 1
fi

# Initialize
echo "📦 Initializing OpenTofu..."
tofu init

# Plan
echo "📋 Planning infrastructure..."
tofu plan -out=tfplan

# Apply
echo "⚡ Applying infrastructure..."
tofu apply tfplan

# Show outputs
echo ""
echo "✅ Deployment complete!"
echo ""
tofu output

echo ""
echo "🎯 Next steps:"
echo "  1. Build and push Docker image to ECR"
echo "  2. Update ECS service with new task definition"
echo "  3. Configure custom domain"
"""

        script_path = self.output_dir / 'deploy.sh'
        script_path.write_text(script)
        script_path.chmod(0o755)  # Make executable
        return script_path

    def _load_pattern(self, pattern: str) -> Dict[str, Any]:
        """Load pattern-specific configuration"""
        if pattern == 'small-saas':
            return {
                'aws': {
                    'instance_sizes': {
                        'database': 'db.t4g.micro',
                        'application': 't3.micro',
                    },
                    'multi_az': False,
                    'autoscaling': {
                        'min': 2,
                        'max': 10,
                    }
                }
            }
        elif pattern == 'production-saas':
            return {
                'aws': {
                    'instance_sizes': {
                        'database': 'db.m5.large',
                        'application': 't3.medium',
                    },
                    'multi_az': True,
                    'autoscaling': {
                        'min': 5,
                        'max': 50,
                    }
                }
            }
        else:
            raise ValueError(f"Unknown pattern: {pattern}")
```

### 2. RDS Module Generator

```python
# src/generators/deployment/opentofu/modules/database/rds_generator.py
from pathlib import Path
from typing import Dict, Any

class RDSGenerator:
    """Generate RDS PostgreSQL module"""

    def __init__(self, config: Dict[str, Any], pattern_config: Dict[str, Any]):
        self.config = config
        self.pattern_config = pattern_config

    def generate(self, output_dir: Path) -> Dict[str, Path]:
        """Generate RDS module files"""
        generated = {}

        # main.tf
        generated['main'] = self._generate_main(output_dir)
        # variables.tf
        generated['variables'] = self._generate_variables(output_dir)
        # outputs.tf
        generated['outputs'] = self._generate_outputs(output_dir)

        return generated

    def _generate_main(self, output_dir: Path) -> Path:
        """Generate RDS main.tf"""
        main_tf = """# ============================================
# RDS PostgreSQL Module
# ============================================

resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.app_name}-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.app_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-rds-sg"
  }
}

# RDS Parameter Group with SpecQL/FraiseQL optimizations
resource "aws_db_parameter_group" "main" {
  name   = "${var.app_name}-postgres"
  family = "postgres16"

  # Connection pooling optimizations
  parameter {
    name  = "max_connections"
    value = "200"
  }

  # Memory optimizations for FraiseQL JSONB queries
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4096}"  # 25% of RAM
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}"  # 50% of RAM
  }

  # Query performance
  parameter {
    name  = "random_page_cost"
    value = "1.1"  # SSD optimization
  }

  # JSONB optimizations (FraiseQL-specific)
  parameter {
    name  = "work_mem"
    value = "16384"  # 16MB for JSONB operations
  }

  # Logging for debugging
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries > 1s
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  tags = {
    Name = "${var.app_name}-postgres"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-postgres"

  # Engine
  engine               = "postgres"
  engine_version       = var.db_engine_version
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true

  # Database
  db_name  = replace(var.app_name, "-", "_")
  username = var.db_username
  password = var.db_password

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = var.multi_az

  # Backups
  backup_retention_period = var.backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.app_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Best practices
  auto_minor_version_upgrade = true
  deletion_protection       = var.environment == "production" ? true : false
  copy_tags_to_snapshot     = true

  # Parameters
  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Name = "${var.app_name}-postgres"
  }
}

# Outputs for connection string construction
locals {
  connection_url = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
}
"""

        main_path = output_dir / 'main.tf'
        main_path.write_text(main_tf)
        return main_path

    def _generate_variables(self, output_dir: Path) -> Path:
        """Generate RDS variables.tf"""
        variables_tf = """# ============================================
# RDS Module Variables
# ============================================

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for RDS"
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Application security group ID"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "db_allocated_storage" {
  description = "Allocated storage (GB)"
  type        = number
}

variable "db_engine_version" {
  description = "PostgreSQL version"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "multi_az" {
  description = "Enable Multi-AZ"
  type        = bool
}

variable "backup_retention_days" {
  description = "Backup retention period"
  type        = number
}
"""

        variables_path = output_dir / 'variables.tf'
        variables_path.write_text(variables_tf)
        return variables_path

    def _generate_outputs(self, output_dir: Path) -> Path:
        """Generate RDS outputs.tf"""
        outputs_tf = """# ============================================
# RDS Module Outputs
# ============================================

output "endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "connection_url" {
  description = "Database connection URL"
  value       = local.connection_url
  sensitive   = true
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}
"""

        outputs_path = output_dir / 'outputs.tf'
        outputs_path.write_text(outputs_tf)
        return outputs_path
```

---

## 📊 Testing Strategy

### Unit Tests

```python
# tests/unit/generators/deployment/opentofu/test_opentofu_orchestrator.py
import pytest
from pathlib import Path
from src.generators.deployment.opentofu.opentofu_orchestrator import OpenTofuOrchestrator

def test_orchestrator_generates_all_files(tmp_path):
    """Test that all expected files are generated"""
    config = {
        'deployment': {'name': 'test-app', 'framework': 'fraiseql'},
        'platform': {'provider': 'aws', 'region': 'us-east-1', 'availability_zones': 2},
        'database': {'engine': 'postgresql', 'version': '16', 'storage': 100},
        'application': {'instances': 2, 'cpu': 0.5, 'memory': 512}
    }

    orchestrator = OpenTofuOrchestrator(
        deployment_config=config,
        pattern='small-saas',
        output_dir=tmp_path
    )

    generated = orchestrator.generate()

    # Verify core files
    assert 'main' in generated
    assert 'variables' in generated
    assert 'outputs' in generated

    # Verify module files
    assert 'rds_module' in generated
    assert 'ecs_module' in generated

def test_main_tf_includes_all_modules():
    """main.tf should include all required modules"""
    config = {...}  # Minimal config

    orchestrator = OpenTofuOrchestrator(config, 'small-saas', Path('/tmp'))
    main_path = orchestrator._generate_main()

    main_content = main_path.read_text()

    assert 'module "networking"' in main_content
    assert 'module "database"' in main_content
    assert 'module "compute"' in main_content
    assert 'module "loadbalancer"' in main_content
    assert 'module "monitoring"' in main_content

def test_small_saas_uses_correct_instance_sizes():
    """small-saas should use cost-optimized instances"""
    config = {...}  # Minimal config

    orchestrator = OpenTofuOrchestrator(config, 'small-saas', Path('/tmp'))

    variables = orchestrator._generate_variables()
    variables_content = variables.read_text()

    assert 'db.t4g.micro' in variables_content  # Small RDS
```

### Integration Tests

```python
# tests/integration/deployment/opentofu/test_opentofu_validation.py
import subprocess

def test_generated_opentofu_validates(tmp_path):
    """Test that generated OpenTofu config validates"""
    config = {...}  # Full config

    orchestrator = OpenTofuOrchestrator(config, 'small-saas', tmp_path)
    orchestrator.generate()

    # Run tofu validate
    result = subprocess.run(
        ['tofu', 'init'],
        cwd=tmp_path / 'infrastructure' / 'opentofu',
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    result = subprocess.run(
        ['tofu', 'validate'],
        cwd=tmp_path / 'infrastructure' / 'opentofu',
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

def test_opentofu_plan_succeeds(tmp_path):
    """Test that tofu plan succeeds (dry run)"""
    # Requires AWS credentials in CI
    # Skip if not available
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        pytest.skip("AWS credentials not available")

    config = {...}
    orchestrator = OpenTofuOrchestrator(config, 'small-saas', tmp_path)
    orchestrator.generate()

    # Create terraform.tfvars
    tfvars = tmp_path / 'infrastructure' / 'opentofu' / 'terraform.tfvars'
    tfvars.write_text("""
app_name = "test-app"
db_username = "test_user"
db_password = "test_password"
alarm_email = "test@example.com"
""")

    # Run tofu plan
    result = subprocess.run(
        ['tofu', 'init'],
        cwd=tmp_path / 'infrastructure' / 'opentofu',
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    result = subprocess.run(
        ['tofu', 'plan'],
        cwd=tmp_path / 'infrastructure' / 'opentofu',
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

---

## 📝 Deliverables

### Code Files
1. ✅ `src/generators/deployment/opentofu/opentofu_orchestrator.py`
2. ✅ `src/generators/deployment/opentofu/modules/networking/vpc_generator.py`
3. ✅ `src/generators/deployment/opentofu/modules/database/rds_generator.py`
4. ✅ `src/generators/deployment/opentofu/modules/compute/ecs_generator.py`
5. ✅ `src/generators/deployment/opentofu/modules/loadbalancer/alb_generator.py`
6. ✅ `src/generators/deployment/opentofu/modules/monitoring/cloudwatch_generator.py`
7. ✅ `src/generators/deployment/opentofu/patterns/small_saas.py`
8. ✅ `src/generators/deployment/opentofu/patterns/production_saas.py`

### Templates
9. ✅ `src/generators/deployment/opentofu/templates/main.tf.j2`
10. ✅ Module templates for each AWS resource

### Tests
11. ✅ `tests/unit/generators/deployment/opentofu/test_opentofu_orchestrator.py`
12. ✅ `tests/unit/generators/deployment/opentofu/test_rds_generator.py`
13. ✅ `tests/integration/deployment/opentofu/test_opentofu_validation.py`

### Documentation
14. ✅ `docs/guides/DEPLOYMENT_AWS.md` - AWS deployment guide
15. ✅ Auto-generated infrastructure README per project

---

## 🚀 Implementation Phases

### Week 1: OpenTofu Orchestrator + VPC (Days 1-3)
**TDD Cycles for networking foundation**

### Week 2: RDS + Security (Days 4-6)
**TDD Cycles for database module**

### Week 3: ECS + ALB (Days 7-9)
**TDD Cycles for compute and load balancing**

### Week 4: Monitoring + Integration (Days 10-12)
**TDD Cycles for observability + E2E tests**

---

## ✅ Success Metrics

### Quantitative
- ✅ Generate complete AWS infrastructure from 20-line YAML
- ✅ `tofu validate` passes with no errors
- ✅ `tofu plan` succeeds in < 30 seconds
- ✅ Cost estimate within 10% of actual AWS costs
- ✅ 100% test coverage for generators
- ✅ Infrastructure deploys successfully in < 10 minutes

### Qualitative
- ✅ Users can deploy to AWS without DevOps expertise
- ✅ Generated infrastructure passes AWS Well-Architected Review
- ✅ Security best practices enforced (encryption, private subnets, IAM)
- ✅ Documentation is clear and complete
- ✅ Cost-optimized for each pattern

---

## 🔗 Dependencies

### Internal
- ✅ Phase 1 (Docker) - For container definitions
- ✅ Framework defaults - For framework-specific optimizations

### External
- **OpenTofu** - Infrastructure as code tool
- **AWS CLI** - For AWS operations
- **jinja2** - Template engine

### Prerequisites
- AWS account with appropriate permissions
- OpenTofu installed locally

---

## 🚧 Risk Mitigation

### High Risk: AWS API Changes
**Mitigation**: Pin OpenTofu provider versions, test on staging first

### Medium Risk: Cost Overruns
**Mitigation**: Provide clear cost estimates, set billing alerts

### Low Risk: OpenTofu Version Compatibility
**Mitigation**: Specify minimum version requirements

---

**Status**: Ready for Implementation (After Phase 1)
**Priority**: HIGH - Critical for production deployments
**Estimated Effort**: 4 weeks (phased TDD approach)
**Risk Level**: High - Cloud infrastructure complexity
