"""
Terraform AWS Generator

Generates Terraform configuration for AWS from universal infrastructure format.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, DatabaseType


class TerraformAWSGenerator:
    """Generate Terraform configuration for AWS from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("terraform_aws.tf.j2")

        # Add custom filters
        self.env.filters["map_instance_type"] = self._map_instance_type
        self.env.filters["map_database_engine"] = self._map_database_engine

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Terraform configuration for AWS"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_instance_type=self._map_instance_type,
            _map_database_engine=self._map_database_engine
        )

    def _map_instance_type(self, compute_config) -> str:
        """Map universal compute config to AWS instance type"""
        if compute_config.instance_type:
            return compute_config.instance_type

        cpu = compute_config.cpu
        memory_gb = int(compute_config.memory.replace("GB", "").replace("MB", "")) / 1000 if "MB" in compute_config.memory else int(compute_config.memory.replace("GB", ""))

        if cpu <= 1 and memory_gb <= 2:
            return "t3.small"
        elif cpu <= 2 and memory_gb <= 4:
            return "t3.medium"
        elif cpu <= 4 and memory_gb <= 8:
            return "t3.large"
        else:
            return "t3.xlarge"

    def _map_database_engine(self, db_type: DatabaseType) -> str:
        """Map universal database type to AWS RDS engine"""
        engine_map = {
            DatabaseType.POSTGRESQL: "postgres",
            DatabaseType.MYSQL: "mysql",
            DatabaseType.REDIS: "redis",
            DatabaseType.ELASTICSEARCH: "elasticsearch",
        }
        return engine_map.get(db_type, "postgres")