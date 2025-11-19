"""
Kubernetes Generator

Generates Kubernetes manifests from universal infrastructure format.
"""

import base64
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.infrastructure.universal_infra_schema import UniversalInfrastructure


class KubernetesGenerator:
    """Generate Kubernetes manifests from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "infrastructure"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        # Add base64 filter for secrets
        self.env.filters['b64encode'] = lambda x: base64.b64encode(x.encode('utf-8')).decode('utf-8')
        self.template = self.env.get_template("kubernetes.yaml.j2")

    def generate(self, infrastructure: UniversalInfrastructure) -> str:
        """Generate Kubernetes manifests"""
        return self.template.render(infrastructure=infrastructure)