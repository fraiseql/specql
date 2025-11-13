"""
Hetzner Generator

Generates provisioning scripts and configurations for Hetzner Cloud bare metal servers.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


class HetznerGenerator:
    """Generate Hetzner provisioning scripts from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("hetzner_provision.sh.j2")

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Hetzner provisioning script"""
        return self.template.render(
            infrastructure=infrastructure,
            _map_server_type=self._map_server_type,
            _get_image=self._get_image,
            _get_datacenter=self._get_datacenter
        )

    def _map_server_type(self, bare_metal_config) -> str:
        """Map universal config to Hetzner server type"""
        if bare_metal_config.server_model:
            return bare_metal_config.server_model

        # Auto-select based on specs
        cpu = bare_metal_config.cpu_cores
        ram = bare_metal_config.ram_gb

        if cpu >= 16 and ram >= 64:
            return "cx52"  # 16 vCPU, 64 GB RAM
        elif cpu >= 8 and ram >= 32:
            return "cx42"  # 8 vCPU, 32 GB RAM
        elif cpu >= 4 and ram >= 16:
            return "cx32"  # 4 vCPU, 16 GB RAM
        elif cpu >= 2 and ram >= 8:
            return "cx22"  # 2 vCPU, 8 GB RAM
        else:
            return "cx11"  # 1 vCPU, 2 GB RAM

    def _get_image(self, os: str) -> str:
        """Get Hetzner image identifier"""
        image_map = {
            "ubuntu2204": "ubuntu-22.04",
            "ubuntu2004": "ubuntu-20.04",
            "debian11": "debian-11",
            "debian10": "debian-10",
            "centos7": "centos-7",
            "centos8": "centos-8",
            "fedora35": "fedora-35",
            "fedora36": "fedora-36",
        }
        return image_map.get(os, "ubuntu-22.04")

    def _get_datacenter(self, region: str, datacenter: Optional[str]) -> str:
        """Get Hetzner datacenter"""
        if datacenter:
            return datacenter

        # Map region to default datacenter
        region_map = {
            "us-east-1": "ash",
            "us-west-1": "hil",
            "eu-west-1": "nbg1",
            "eu-central-1": "fsn1",
            "ap-southeast-1": "sin",
        }
        return region_map.get(region, "nbg1")