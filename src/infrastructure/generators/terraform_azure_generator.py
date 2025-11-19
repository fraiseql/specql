"""
Terraform Azure Generator

Generates Terraform configuration for Microsoft Azure from universal infrastructure format.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class TerraformAzureGenerator:
    """Generate Terraform configuration for Azure from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("terraform_azure.tf.j2")

        # Add custom filters
        self.env.filters["map_instance_type"] = self._map_instance_type
        self.env.filters["map_database_engine"] = self._map_database_engine
        self.env.filters["map_region"] = self._map_region

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Terraform configuration for Azure"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_instance_type=self._map_instance_type,
            _map_database_engine=self._map_database_engine,
            _map_region=self._map_region
        )

    def _map_instance_type(self, compute_config) -> str:
        """Map universal compute config to Azure VM size"""
        if compute_config.instance_type:
            return compute_config.instance_type

        cpu = compute_config.cpu
        memory_gb = int(compute_config.memory.replace("GB", "").replace("MB", "")) / 1000 if "MB" in compute_config.memory else int(compute_config.memory.replace("GB", ""))

        if cpu <= 1 and memory_gb <= 2:
            return "Standard_B1s"
        elif cpu <= 2 and memory_gb <= 4:
            return "Standard_B2s"
        elif cpu <= 2 and memory_gb <= 8:
            return "Standard_B2ms"
        elif cpu <= 4 and memory_gb <= 16:
            return "Standard_B4ms"
        else:
            return "Standard_B8ms"

    def _map_database_engine(self, db_type: DatabaseType) -> str:
        """Map universal database type to Azure database engine"""
        engine_map = {
            DatabaseType.POSTGRESQL: "PostgreSQL",
            DatabaseType.MYSQL: "MySQL",
            DatabaseType.MONGODB: "MongoDB",  # Azure Cosmos DB with MongoDB API
            DatabaseType.REDIS: "RedisCache",
            DatabaseType.ELASTICSEARCH: "Search",  # Azure Cognitive Search
        }
        return engine_map.get(db_type, "PostgreSQL")

    def _map_region(self, region: str) -> str:
        """Map universal region to Azure region"""
        # Azure regions are similar to AWS, but some mappings needed
        region_map = {
            "us-east-1": "East US",
            "us-west-1": "West US",
            "us-west-2": "West US 2",
            "eu-west-1": "North Europe",
            "eu-central-1": "Germany West Central",
            "ap-southeast-1": "Southeast Asia",
            "ap-northeast-1": "Japan East",
        }
        return region_map.get(region, region)