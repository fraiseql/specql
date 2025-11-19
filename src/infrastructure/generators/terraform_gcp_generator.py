"""
Terraform GCP Generator

Generates Terraform configuration for Google Cloud Platform from universal infrastructure format.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class TerraformGCPGenerator:
    """Generate Terraform configuration for GCP from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("terraform_gcp.tf.j2")

        # Add custom filters
        self.env.filters["map_instance_type"] = self._map_instance_type
        self.env.filters["map_database_engine"] = self._map_database_engine
        self.env.filters["map_region"] = self._map_region

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Terraform configuration for GCP"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_instance_type=self._map_instance_type,
            _map_database_engine=self._map_database_engine,
            _map_region=self._map_region
        )

    def _map_instance_type(self, compute_config) -> str:
        """Map universal compute config to GCP instance type"""
        if compute_config.instance_type:
            return compute_config.instance_type

        cpu = compute_config.cpu
        memory_gb = int(compute_config.memory.replace("GB", "").replace("MB", "")) / 1000 if "MB" in compute_config.memory else int(compute_config.memory.replace("GB", ""))

        if cpu <= 1 and memory_gb <= 2:
            return "e2-micro"
        elif cpu <= 2 and memory_gb <= 4:
            return "e2-small"
        elif cpu <= 2 and memory_gb <= 8:
            return "e2-medium"
        elif cpu <= 4 and memory_gb <= 16:
            return "e2-standard-4"
        else:
            return "e2-standard-8"

    def _map_database_engine(self, db_type: DatabaseType) -> str:
        """Map universal database type to GCP database engine"""
        engine_map = {
            DatabaseType.POSTGRESQL: "POSTGRES_15",
            DatabaseType.MYSQL: "MYSQL_8_0",
            DatabaseType.REDIS: "REDIS_7_0",
            DatabaseType.ELASTICSEARCH: "elasticsearch",  # GCP doesn't have native ES, would need separate service
        }
        return engine_map.get(db_type, "POSTGRES_15")

    def _map_region(self, region: str) -> str:
        """Map universal region to GCP region"""
        # GCP regions are similar to AWS, but some mappings needed
        region_map = {
            "us-east-1": "us-east1",
            "us-west-1": "us-west1",
            "us-west-2": "us-west2",
            "eu-west-1": "europe-west1",
            "eu-central-1": "europe-west3",
            "ap-southeast-1": "asia-southeast1",
            "ap-northeast-1": "asia-northeast1",
        }
        return region_map.get(region, region)