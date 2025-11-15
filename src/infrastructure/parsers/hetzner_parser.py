"""
Hetzner Parser

Reverse engineers Hetzner configurations to universal infrastructure format.
Parses Hetzner API responses, CLI output, or configuration files.
"""

import json
from typing import Dict, Any
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    BareMetalConfig,
    CloudProvider,
    ContainerConfig,
)


class HetznerParser:
    """Parse Hetzner configurations to universal format"""

    def parse_dedicated_server(
        self, server_data: Dict[str, Any]
    ) -> UniversalInfrastructure:
        """
        Parse Hetzner dedicated server data to UniversalInfrastructure

        Args:
            server_data: Hetzner API response or CLI output for a dedicated server

        Returns:
            UniversalInfrastructure object with bare_metal config
        """
        # Extract server information
        server_name = server_data.get(
            "name", server_data.get("hostname", "hetzner-server")
        )
        datacenter = server_data.get(
            "datacenter", server_data.get("location", {}).get("name", "nbg1")
        )

        # Hetzner uses server_type instead of model
        server_type = server_data.get("server_type", server_data.get("type", "cx11"))

        # Map Hetzner server type to specs
        cpu_cores, ram_gb, storage_gb = self._map_server_specs(server_type, server_data)

        # Extract OS information
        os = self._extract_os(server_data)

        # Create bare metal config
        bare_metal = BareMetalConfig(
            server_model=server_type,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            storage_type="ssd",  # Hetzner typically uses SSD/NVMe
            storage_gb=storage_gb,
            os=os,
            ssh_keys=[],  # Would need to be extracted from separate API calls
        )

        # Create universal infrastructure
        infra = UniversalInfrastructure(
            name=server_name,
            description=f"Hetzner dedicated server {server_type}",
            service_type="api",
            provider=CloudProvider.HETZNER,
            region=datacenter,
            environment="production",
            bare_metal=bare_metal,
        )

        # Add container if present
        if "containers" in server_data or "docker" in server_data:
            container_data = server_data.get(
                "containers", server_data.get("docker", {})
            )
            if container_data:
                infra.container = ContainerConfig(
                    image=container_data.get("image", "nginx:latest"),
                    tag=container_data.get("tag", "latest"),
                    port=container_data.get("port", 80),
                    environment=container_data.get("environment", {}),
                )

        return infra

    def parse_from_api_response(self, api_response: str) -> UniversalInfrastructure:
        """
        Parse Hetzner API JSON response

        Args:
            api_response: JSON string from Hetzner API

        Returns:
            UniversalInfrastructure object
        """
        try:
            data = json.loads(api_response)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from Hetzner API")

        # Hetzner API wraps server data in "server" key
        server_data = data.get("server", data)
        return self.parse_dedicated_server(server_data)

    def parse_from_cli_output(self, cli_output: str) -> UniversalInfrastructure:
        """
        Parse Hetzner CLI output

        Args:
            cli_output: Output from hcloud CLI commands

        Returns:
            UniversalInfrastructure object
        """
        # Parse CLI output format (simplified - would need to handle actual CLI formats)
        lines = cli_output.strip().split("\n")
        server_data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_").replace("-", "_")
                value = value.strip()
                server_data[key] = value

        return self.parse_dedicated_server(server_data)

    def _extract_os(self, server_data: Dict[str, Any]) -> str:
        """Extract OS information from server data"""
        os_info = server_data.get("os", server_data.get("image", {}))

        if isinstance(os_info, dict):
            os_name = os_info.get("name", "").lower()
        else:
            os_name = str(os_info).lower()

        # Map to universal OS identifiers
        if "ubuntu" in os_name:
            if "22" in os_name or "jammy" in os_name:
                return "ubuntu2204"
            elif "20" in os_name or "focal" in os_name:
                return "ubuntu2004"
            else:
                return "ubuntu2204"
        elif "debian" in os_name:
            if "11" in os_name or "bullseye" in os_name:
                return "debian11"
            elif "10" in os_name or "buster" in os_name:
                return "debian10"
            else:
                return "debian11"
        elif "centos" in os_name:
            return "centos8"
        elif "fedora" in os_name:
            return "fedora36"
        else:
            return "ubuntu2204"  # Default

    def _map_server_specs(
        self, server_type: str, server_data: Dict[str, Any]
    ) -> tuple[int, int, int]:
        """Map Hetzner server type to CPU cores, RAM GB, and storage GB"""
        # Hetzner dedicated server type mappings (approximate)
        type_specs = {
            "ax41": (4, 16, 80),  # AX41
            "ax101": (8, 32, 160),  # AX101
            "ax161": (16, 64, 320),  # AX161
            "px92": (4, 16, 80),  # PX92
            "px132": (8, 32, 160),  # PX132
            # Cloud servers (for completeness)
            "cx11": (1, 2, 20),
            "cx21": (2, 4, 40),
            "cx31": (2, 8, 80),
            "cx41": (4, 16, 160),
            "cx51": (8, 32, 240),
            "cx52": (16, 64, 320),
        }

        # Try to get from type mapping
        if server_type in type_specs:
            return type_specs[server_type]

        # Fallback to extracting from server data
        cpu_cores = server_data.get("cpu", {}).get("cores", 4)
        ram_gb = (
            server_data.get("memory", {}).get("size", 16) // 1024 // 1024 // 1024
        )  # Convert bytes to GB
        storage_gb = 0

        # Sum up storage
        storages = server_data.get("storages", server_data.get("volumes", []))
        if isinstance(storages, list):
            for storage in storages:
                if isinstance(storage, dict):
                    storage_gb += (
                        storage.get("size", 0) // 1024 // 1024 // 1024
                    )  # Convert bytes to GB

        return cpu_cores, max(ram_gb, 1), max(storage_gb, 20)
