"""
OVHcloud Generator

Generates provisioning scripts and configurations for OVHcloud bare metal servers.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


class OVHcloudGenerator:
    """Generate OVHcloud provisioning scripts from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("ovhcloud_provision.sh.j2")

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate OVHcloud provisioning script"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_server_model=self._map_server_model,
            _get_os_template=self._get_os_template,
            _get_datacenter=self._get_datacenter
        )

    def _map_server_model(self, bare_metal_config) -> str:
        """Map universal config to OVHcloud server model"""
        if bare_metal_config.server_model:
            return bare_metal_config.server_model

        # Auto-select based on specs
        cpu = bare_metal_config.cpu_cores
        ram = bare_metal_config.ram_gb

        if cpu >= 16 and ram >= 64:
            return "RISE-2"
        elif cpu >= 8 and ram >= 32:
            return "RISE-1"
        elif cpu >= 4 and ram >= 16:
            return "ADVANCE-3"
        elif cpu >= 2 and ram >= 8:
            return "ADVANCE-2"
        else:
            return "ADVANCE-1"

    def _get_os_template(self, os: str) -> str:
        """Get OVHcloud OS template identifier"""
        os_map = {
            "ubuntu2204": "ubuntu2204-server_64",
            "ubuntu2004": "ubuntu2004-server_64",
            "debian11": "debian11_64",
            "debian10": "debian10_64",
            "centos7": "centos7_64",
            "centos8": "centos8_64",
            "windows2019": "windows2019std_64",
            "windows2022": "windows2022std_64",
        }
        return os_map.get(os, "ubuntu2204-server_64")

    def _get_datacenter(self, region: str, datacenter: Optional[str]) -> str:
        """Get OVHcloud datacenter"""
        if datacenter:
            return datacenter

        # Map region to default datacenter
        region_map = {
            "us-east-1": "US-EAST-VA-1",
            "us-west-1": "US-WEST-LA-1",
            "eu-west-1": "EU-WEST-GRA-1",
            "eu-central-1": "EU-CENTRAL-WAW-1",
            "ap-southeast-1": "AP-SOUTHEAST-SGP-1",
        }
        return region_map.get(region, "EU-WEST-GRA-1")