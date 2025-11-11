"""Service registry for external service integrations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class ServiceOperation:
    name: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    timeout: int = 30
    max_retries: int = 3

    def validate_input_schema(self) -> None:
        """Validate input schema has required fields"""
        if not isinstance(self.input_schema, dict):
            raise ValueError(f"input_schema must be a dict for operation {self.name}")

    def validate_output_schema(self) -> None:
        """Validate output schema has required fields"""
        if not isinstance(self.output_schema, dict):
            raise ValueError(f"output_schema must be a dict for operation {self.name}")


@dataclass
class Service:
    name: str
    type: str  # email, payment, webhook, notification
    category: str  # communication, financial, integration
    operations: List[ServiceOperation]

    def has_operation(self, operation_name: str) -> bool:
        return any(op.name == operation_name for op in self.operations)

    def get_operation(self, operation_name: str) -> ServiceOperation:
        for op in self.operations:
            if op.name == operation_name:
                return op
        raise ValueError(f"Operation '{operation_name}' not found in service '{self.name}'")

    def validate_operations(self) -> None:
        """Validate all operations have proper schemas"""
        for op in self.operations:
            op.validate_input_schema()
            op.validate_output_schema()


@dataclass
class ServiceRegistry:
    """
    Load and manage service registry for external integrations

    Responsibilities:
    - Load registry from YAML
    - Index services for fast lookup
    - Validate service configurations
    - Provide service discovery
    """

    services: List[Service]
    services_index: Dict[str, Service] = None  # type: ignore

    def __post_init__(self):
        """Build index after initialization"""
        self._build_services_index()

    def _build_services_index(self) -> None:
        """Build index of services for O(1) lookup"""
        self.services_index = {}
        for service in self.services:
            self.services_index[service.name.lower()] = service

    @classmethod
    def from_yaml(cls, path: str) -> "ServiceRegistry":
        """Load service registry from YAML file"""
        registry_path = Path(path)
        if not registry_path.exists():
            raise FileNotFoundError(
                f"Service registry not found: {registry_path}\n"
                f"Create it by defining services in {path}"
            )

        with open(registry_path) as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Service registry is empty: {path}")

        services = []
        for service_data in data.get("services", []):
            # Validate required fields
            required_fields = ["name", "type", "category", "operations"]
            for field in required_fields:
                if field not in service_data:
                    raise ValueError(f"Service missing required field '{field}': {service_data}")

            operations = []
            for op_data in service_data.get("operations", []):
                if "name" not in op_data:
                    raise ValueError(f"Operation missing required field 'name': {op_data}")

                operation = ServiceOperation(
                    name=op_data["name"],
                    input_schema=op_data.get("input_schema", {}),
                    output_schema=op_data.get("output_schema", {}),
                    timeout=op_data.get("timeout", 30),
                    max_retries=op_data.get("max_retries", 3),
                )
                operations.append(operation)

            service = Service(
                name=service_data["name"],
                type=service_data["type"],
                category=service_data["category"],
                operations=operations,
            )

            # Validate the service
            service.validate_operations()
            services.append(service)

        return cls(services=services)

    def get_service(self, name: str) -> Service:
        """
        Get service by name (case-insensitive)

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            ValueError: If service not found
        """
        service = self.services_index.get(name.lower())
        if service is None:
            available = list(self.services_index.keys())
            raise ValueError(f"Service '{name}' not found. Available: {available}")
        return service
