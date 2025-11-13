"""
Cost Estimation Service

Provides cost estimation for infrastructure across multiple cloud providers.
"""

from dataclasses import dataclass
from typing import Dict, Any
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    CloudProvider,
    ComputeConfig,
    DatabaseConfig,
    LoadBalancerConfig,
    BareMetalConfig
)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown by resource type"""
    compute_cost: float = 0.0
    database_cost: float = 0.0
    storage_cost: float = 0.0
    network_cost: float = 0.0
    load_balancer_cost: float = 0.0
    monitoring_cost: float = 0.0
    total_monthly_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compute_cost": round(self.compute_cost, 2),
            "database_cost": round(self.database_cost, 2),
            "storage_cost": round(self.storage_cost, 2),
            "network_cost": round(self.network_cost, 2),
            "load_balancer_cost": round(self.load_balancer_cost, 2),
            "monitoring_cost": round(self.monitoring_cost, 2),
            "total_monthly_cost": round(self.total_monthly_cost, 2)
        }


class CostEstimationService:
    """Service for estimating infrastructure costs across cloud providers"""

    def __init__(self):
        # Load pricing data (in a real implementation, this would come from APIs)
        self.pricing_data = self._load_pricing_data()

    def _load_pricing_data(self) -> Dict[str, Any]:
        """Load pricing data for different cloud providers"""
        # For now, using static pricing data
        # In production, this would fetch from cloud provider pricing APIs
        return {
            "aws": {
                "ec2": {
                    "t3.micro": 0.0104,  # per hour
                    "t3.small": 0.0208,
                    "t3.medium": 0.0416,
                    "t3.large": 0.0832,
                    "t3.xlarge": 0.1664,
                },
                "rds": {
                    "postgresql": {
                        "db.t3.micro": 0.017,  # per hour
                        "db.t3.small": 0.034,
                        "db.t3.medium": 0.068,
                        "db.t3.large": 0.136,
                    }
                },
                "storage": {
                    "gp3": 0.08,  # per GB/month
                    "io1": 0.125,
                },
                "load_balancer": {
                    "application": 0.0225,  # per hour
                },
                "data_transfer": {
                    "out": 0.09,  # per GB
                }
            },
            "gcp": {
                "compute": {
                    "e2-micro": 0.0077,  # per hour
                    "e2-small": 0.0154,
                    "e2-medium": 0.0307,
                    "e2-standard-2": 0.0614,
                    "e2-standard-4": 0.1228,
                },
                "cloud_sql": {
                    "postgresql": {
                        "db-f1-micro": 0.015,  # per hour
                        "db-g1-small": 0.030,
                    }
                },
                "storage": {
                    "pd-standard": 0.040,  # per GB/month
                    "pd-ssd": 0.170,
                },
                "load_balancer": {
                    "external": 0.025,  # per GB
                }
            },
            "azure": {
                "vm": {
                    "Standard_B1s": 0.0104,  # per hour
                    "Standard_B1ms": 0.0207,
                    "Standard_B2s": 0.0415,
                    "Standard_B2ms": 0.083,
                },
                "database": {
                    "postgresql": {
                        "B_Gen5_1": 0.0208,  # per hour
                        "B_Gen5_2": 0.0416,
                        "GP_Gen5_2": 0.0832,
                    }
                },
                "storage": {
                    "standard": 0.0184,  # per GB/month
                    "premium": 0.0307,
                },
                "load_balancer": {
                    "basic": 0.025,  # per hour
                }
            },
            "ovhcloud": {
                "bare_metal": {
                    "ADVANCE-1": 30.0,  # per month
                    "ADVANCE-2": 60.0,
                    "ADVANCE-3": 120.0,
                    "RISE-1": 80.0,
                    "RISE-2": 160.0,
                }
            },
            "hetzner": {
                "bare_metal": {
                    "AX41": 50.0,  # per month
                    "AX101": 100.0,
                    "AX161": 150.0,
                    "PX92": 80.0,
                    "PX132": 120.0,
                }
            }
        }

    def estimate_cost(self, infrastructure: UniversalInfrastructure) -> CostBreakdown:
        """Estimate monthly cost for the given infrastructure"""
        breakdown = CostBreakdown()

        provider = infrastructure.provider.value

        # Bare metal costs
        if infrastructure.bare_metal:
            breakdown.compute_cost = self._estimate_bare_metal_cost(infrastructure.bare_metal, provider)
        # Compute costs
        elif infrastructure.compute:
            breakdown.compute_cost = self._estimate_compute_cost(infrastructure.compute, provider)

        # Database costs
        if infrastructure.database:
            breakdown.database_cost = self._estimate_database_cost(infrastructure.database, provider)

        # Storage costs
        breakdown.storage_cost = self._estimate_storage_cost(infrastructure, provider)

        # Load balancer costs
        if infrastructure.load_balancer:
            breakdown.load_balancer_cost = self._estimate_load_balancer_cost(infrastructure.load_balancer, provider)

        # Network costs (simplified)
        breakdown.network_cost = self._estimate_network_cost(infrastructure, provider)

        # Monitoring costs (simplified)
        breakdown.monitoring_cost = self._estimate_monitoring_cost(infrastructure, provider)

        # Calculate total
        breakdown.total_monthly_cost = (
            breakdown.compute_cost +
            breakdown.database_cost +
            breakdown.storage_cost +
            breakdown.network_cost +
            breakdown.load_balancer_cost +
            breakdown.monitoring_cost
        )

        return breakdown

    def _estimate_compute_cost(self, compute: ComputeConfig, provider: str) -> float:
        """Estimate compute instance costs"""
        if provider not in self.pricing_data:
            return 0.0

        # Map instance type or calculate based on specs
        hourly_rate = 0.0

        if compute.instance_type:
            # Use specific instance type if provided
            instance_key = compute.instance_type
            if provider == "aws":
                hourly_rate = self.pricing_data["aws"]["ec2"].get(instance_key, 0.0)
            elif provider == "gcp":
                hourly_rate = self.pricing_data["gcp"]["compute"].get(instance_key, 0.0)
            elif provider == "azure":
                hourly_rate = self.pricing_data["azure"]["vm"].get(instance_key, 0.0)
        else:
            # Estimate based on CPU/memory specs
            if provider == "aws":
                # Rough mapping for AWS
                if compute.cpu <= 1 and compute.memory.startswith("2"):
                    hourly_rate = 0.0104  # t3.micro
                elif compute.cpu <= 2 and compute.memory.startswith("4"):
                    hourly_rate = 0.0208  # t3.small
                elif compute.cpu <= 2 and compute.memory.startswith("8"):
                    hourly_rate = 0.0416  # t3.medium
                else:
                    hourly_rate = 0.0832  # t3.large
            elif provider == "gcp":
                if compute.cpu <= 1 and compute.memory.startswith("2"):
                    hourly_rate = 0.0077  # e2-micro
                elif compute.cpu <= 2 and compute.memory.startswith("4"):
                    hourly_rate = 0.0154  # e2-small
                else:
                    hourly_rate = 0.0307  # e2-medium
            elif provider == "azure":
                if compute.cpu <= 1 and compute.memory.startswith("1"):
                    hourly_rate = 0.0104  # B1s
                elif compute.cpu <= 2 and compute.memory.startswith("2"):
                    hourly_rate = 0.0207  # B1ms
                else:
                    hourly_rate = 0.0415  # B2s

        # Calculate monthly cost (24 hours * 30 days)
        instances = compute.instances
        monthly_hours = 24 * 30
        return hourly_rate * instances * monthly_hours

    def _estimate_database_cost(self, database: DatabaseConfig, provider: str) -> float:
        """Estimate database costs"""
        if provider not in self.pricing_data:
            return 0.0

        hourly_rate = 0.0

        if database.instance_class:
            # Use specific instance class
            if provider == "aws":
                hourly_rate = self.pricing_data["aws"]["rds"]["postgresql"].get(database.instance_class, 0.0)
            elif provider == "gcp":
                hourly_rate = self.pricing_data["gcp"]["cloud_sql"]["postgresql"].get(database.instance_class, 0.0)
            elif provider == "azure":
                hourly_rate = self.pricing_data["azure"]["database"]["postgresql"].get(database.instance_class, 0.0)
        else:
            # Default to small instance
            if provider == "aws":
                hourly_rate = 0.017  # db.t3.micro
            elif provider == "gcp":
                hourly_rate = 0.015  # db-f1-micro
            elif provider == "azure":
                hourly_rate = 0.0208  # B_Gen5_1

        # Storage costs
        storage_gb = int(database.storage.replace("GB", "").replace("TB", "000"))
        storage_cost_per_gb = 0.0

        if provider == "aws":
            storage_cost_per_gb = self.pricing_data["aws"]["storage"].get(database.storage_type, 0.08)
        elif provider == "gcp":
            storage_cost_per_gb = self.pricing_data["gcp"]["storage"]["pd-standard"]
        elif provider == "azure":
            storage_cost_per_gb = self.pricing_data["azure"]["storage"]["standard"]

        storage_monthly = storage_gb * storage_cost_per_gb

        # Instance costs (24 hours * 30 days)
        monthly_hours = 24 * 30
        instance_monthly = hourly_rate * monthly_hours

        return instance_monthly + storage_monthly

    def _estimate_storage_cost(self, infrastructure: UniversalInfrastructure, provider: str) -> float:
        """Estimate storage costs for volumes and object storage"""
        if provider not in self.pricing_data:
            return 0.0

        total_cost = 0.0

        # Volume storage
        for volume in infrastructure.volumes:
            size_gb = int(volume.size.replace("GB", "").replace("TB", "000"))
            if provider == "aws":
                cost_per_gb = self.pricing_data["aws"]["storage"]["gp3"]
            elif provider == "gcp":
                cost_per_gb = self.pricing_data["gcp"]["storage"]["pd-standard"]
            elif provider == "azure":
                cost_per_gb = self.pricing_data["azure"]["storage"]["standard"]
            else:
                cost_per_gb = 0.08  # Default

            total_cost += size_gb * cost_per_gb

        return total_cost

    def _estimate_load_balancer_cost(self, load_balancer: LoadBalancerConfig, provider: str) -> float:
        """Estimate load balancer costs"""
        if provider not in self.pricing_data:
            return 0.0

        if provider == "aws":
            hourly_rate = self.pricing_data["aws"]["load_balancer"]["application"]
        elif provider == "gcp":
            # GCP charges per GB processed, estimate 100GB/month
            return self.pricing_data["gcp"]["load_balancer"]["external"] * 100
        elif provider == "azure":
            hourly_rate = self.pricing_data["azure"]["load_balancer"]["basic"]
        else:
            return 0.0

        # Monthly cost
        monthly_hours = 24 * 30
        return hourly_rate * monthly_hours

    def _estimate_network_cost(self, infrastructure: UniversalInfrastructure, provider: str) -> float:
        """Estimate network costs (simplified)"""
        # Simplified: assume some data transfer costs
        if provider == "aws":
            # Estimate 100GB outbound data transfer
            return self.pricing_data["aws"]["data_transfer"]["out"] * 100
        else:
            # Other providers have different pricing, simplified to $10/month
            return 10.0

    def _estimate_bare_metal_cost(self, bare_metal: BareMetalConfig, provider: str) -> float:
        """Estimate bare metal server costs"""
        if provider not in self.pricing_data or "bare_metal" not in self.pricing_data[provider]:
            return 0.0

        monthly_rate = 0.0

        if bare_metal.server_model:
            # Use specific server model if provided
            monthly_rate = self.pricing_data[provider]["bare_metal"].get(bare_metal.server_model, 0.0)
        else:
            # Estimate based on specs (simplified mapping)
            cpu = bare_metal.cpu_cores
            ram = bare_metal.ram_gb

            if provider == "ovhcloud":
                if cpu >= 16 and ram >= 64:
                    monthly_rate = 120.0  # ADVANCE-3 equivalent
                elif cpu >= 8 and ram >= 32:
                    monthly_rate = 80.0   # RISE-1 equivalent
                elif cpu >= 4 and ram >= 16:
                    monthly_rate = 60.0   # ADVANCE-2 equivalent
                else:
                    monthly_rate = 30.0   # ADVANCE-1 equivalent
            elif provider == "hetzner":
                if cpu >= 16 and ram >= 64:
                    monthly_rate = 150.0  # AX161 equivalent
                elif cpu >= 8 and ram >= 32:
                    monthly_rate = 100.0  # AX101 equivalent
                elif cpu >= 4 and ram >= 16:
                    monthly_rate = 80.0   # PX92 equivalent
                else:
                    monthly_rate = 50.0   # AX41 equivalent

        return monthly_rate

    def _estimate_monitoring_cost(self, infrastructure: UniversalInfrastructure, provider: str) -> float:
        """Estimate monitoring costs (simplified)"""
        # Simplified: basic monitoring costs
        if provider == "aws":
            return 5.0  # CloudWatch basic
        elif provider == "gcp":
            return 8.0  # Cloud Monitoring
        elif provider == "azure":
            return 6.0  # Azure Monitor
        else:
            return 5.0

    def get_cost_comparison(self, infrastructure: UniversalInfrastructure) -> Dict[str, CostBreakdown]:
        """Get cost estimates across all supported providers"""
        comparisons = {}

        for provider in ["aws", "gcp", "azure", "ovhcloud", "hetzner"]:
            # Create a copy with different provider
            infra_copy = UniversalInfrastructure(
                name=infrastructure.name,
                description=infrastructure.description,
                service_type=infrastructure.service_type,
                provider=CloudProvider(provider),
                region=infrastructure.region,
                environment=infrastructure.environment,
                compute=infrastructure.compute,
                container=infrastructure.container,
                database=infrastructure.database,
                network=infrastructure.network,
                load_balancer=infrastructure.load_balancer,
                cdn=infrastructure.cdn,
                volumes=infrastructure.volumes,
                object_storage=infrastructure.object_storage,
                observability=infrastructure.observability,
                security=infrastructure.security,
                tags=infrastructure.tags,
                bare_metal=infrastructure.bare_metal,
            )
            comparisons[provider] = self.estimate_cost(infra_copy)

        return comparisons