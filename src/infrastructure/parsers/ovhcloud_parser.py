"""
OVHcloud Parser

Reverse engineers OVHcloud configurations to universal infrastructure format.
Parses OVHcloud API responses, CLI output, or configuration files.
"""

import json
from typing import Dict, Any
from src.infrastructure.universal_infra_schema import (
    UniversalInfrastructure,
    BareMetalConfig,
    CloudProvider,
    ContainerConfig,
)


class OVHcloudParser:
    """Parse OVHcloud configurations to universal format"""

    def parse_dedicated_server(
        self, server_data: Dict[str, Any]
    ) -> UniversalInfrastructure:
        """
        Parse OVHcloud dedicated server data to UniversalInfrastructure

        Args:
            server_data: OVHcloud API response or CLI output for a dedicated server

        Returns:
            UniversalInfrastructure object with bare_metal config
        """
        # Extract server information
        server_name = server_data.get(
            "name", server_data.get("displayName", "ovh-server")
        )
        datacenter = server_data.get("datacenter", server_data.get("region", "GRA1"))
        os = self._extract_os(server_data)

        # Map OVHcloud server model to specs
        server_model = server_data.get("commercialRange", "")
        cpu_cores, ram_gb, storage_gb = self._map_server_specs(
            server_model, server_data
        )

        # Create bare metal config
        bare_metal = BareMetalConfig(
            server_model=server_model,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            storage_type="ssd",  # OVHcloud typically uses SSD or NVMe
            storage_gb=storage_gb,
            os=os,
            ssh_keys=[],  # Would need to be extracted from separate API calls
        )

        # Create universal infrastructure
        infra = UniversalInfrastructure(
            name=server_name,
            description=f"OVHcloud dedicated server {server_model}",
            service_type="api",
            provider=CloudProvider.OVHCLOUD,
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
        Parse OVHcloud API JSON response

        Args:
            api_response: JSON string from OVHcloud API

        Returns:
            UniversalInfrastructure object
        """
        try:
            data = json.loads(api_response)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from OVHcloud API")

        return self.parse_dedicated_server(data)

    def parse_from_cli_output(self, cli_output: str) -> UniversalInfrastructure:
        """
        Parse OVHcloud CLI output

        Args:
            cli_output: Output from OVHcloud CLI commands

        Returns:
            UniversalInfrastructure object
        """
        # Parse CLI output format (simplified - would need to handle actual CLI formats)
        lines = cli_output.strip().split("\n")
        server_data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                server_data[key] = value

        return self.parse_dedicated_server(server_data)

    def _extract_os(self, server_data: Dict[str, Any]) -> str:
        """Extract OS information from server data"""
        os_info = server_data.get("os", server_data.get("operatingSystem", {}))

        if isinstance(os_info, dict):
            os_name = os_info.get("name", "").lower()
        else:
            os_name = str(os_info).lower()

        # Map to universal OS identifiers
        if "ubuntu" in os_name:
            if "22" in os_name:
                return "ubuntu2204"
            elif "20" in os_name:
                return "ubuntu2004"
            else:
                return "ubuntu2204"
        elif "debian" in os_name:
            if "11" in os_name:
                return "debian11"
            elif "10" in os_name:
                return "debian10"
            else:
                return "debian11"
        elif "centos" in os_name:
            return "centos8"
        else:
            return "ubuntu2204"  # Default

    def _map_server_specs(
        self, server_model: str, server_data: Dict[str, Any]
    ) -> tuple[int, int, int]:
        """Map OVHcloud server model to CPU cores, RAM GB, and storage GB"""
        # OVHcloud server model mappings (approximate)
        model_specs = {
            "ADVANCE-1": (2, 8, 40),
            "ADVANCE-2": (4, 16, 80),
            "ADVANCE-3": (8, 32, 160),
            "RISE-1": (8, 32, 240),
            "RISE-2": (16, 64, 480),
            "KS-1": (4, 16, 80),
            "KS-2": (8, 32, 160),
            "KS-3": (16, 64, 320),
            "KS-4": (24, 128, 640),
            "KS-5": (32, 256, 1280),
            "KS-6": (48, 384, 1920),
        }

        # Try to get from model mapping
        if server_model in model_specs:
            return model_specs[server_model]

        # Fallback to extracting from server data
        cpu_cores = server_data.get("cpu", {}).get("cores", 4)
        ram_gb = (
            server_data.get("memory", {}).get("size", 16) // 1024 // 1024 // 1024
        )  # Convert bytes to GB
        storage_gb = 0

        # Sum up storage
        storages = server_data.get("storages", [])
        if isinstance(storages, list):
            for storage in storages:
                if isinstance(storage, dict):
                    storage_gb += (
                        storage.get("size", 0) // 1024 // 1024 // 1024
                    )  # Convert bytes to GB

        return cpu_cores, max(ram_gb, 1), max(storage_gb, 20)
