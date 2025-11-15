"""
CLI commands for infrastructure operations

Usage:
    specql infrastructure reverse-infra terraform.tf --output infra.yaml
    specql infrastructure generate-infra infra.yaml --platform kubernetes
    specql infrastructure convert infra.yaml --from aws --to gcp
"""

import click
from pathlib import Path
from src.infrastructure.parsers.terraform_parser import TerraformParser
from src.infrastructure.parsers.kubernetes_parser import KubernetesParser
from src.infrastructure.parsers.docker_compose_parser import DockerComposeParser
from src.infrastructure.generators.terraform_aws_generator import TerraformAWSGenerator
from src.infrastructure.generators.terraform_gcp_generator import TerraformGCPGenerator
from src.infrastructure.generators.terraform_azure_generator import TerraformAzureGenerator
from src.infrastructure.generators.cloudformation_generator import CloudFormationGenerator
from src.infrastructure.generators.pulumi_generator import PulumiGenerator
from src.infrastructure.generators.kubernetes_generator import KubernetesGenerator
from src.infrastructure.generators.ovhcloud_generator import OVHcloudGenerator
from src.infrastructure.generators.hetzner_generator import HetznerGenerator
from src.infrastructure.universal_infra_schema import UniversalInfrastructure, CloudProvider
import yaml


@click.group()
def infrastructure():
    """Infrastructure operations: reverse engineering, generation, and conversion"""
    pass


@infrastructure.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output YAML file")
@click.option("--format", type=click.Choice(["terraform", "kubernetes", "docker-compose", "ovhcloud", "hetzner"]), default="terraform", help="Input format")
def reverse_infra(input_file, output, format):
    """
    Reverse engineer infrastructure to universal format

    Examples:
        specql infrastructure reverse-infra terraform.tf
        specql infrastructure reverse-infra k8s-manifests/ -o infra.yaml --format kubernetes
        specql infrastructure reverse-infra docker-compose.yml --format docker-compose
    """
    input_path = Path(input_file)

    # Select parser based on format
    if format == "terraform":
        parser = TerraformParser()
    elif format == "kubernetes":
        parser = KubernetesParser()
    elif format == "docker-compose":
        parser = DockerComposeParser()
    elif format == "ovhcloud":
        from src.infrastructure.parsers.ovhcloud_parser import OVHcloudParser
        parser = OVHcloudParser()
    elif format == "hetzner":
        from src.infrastructure.parsers.hetzner_parser import HetznerParser
        parser = HetznerParser()
    else:
        click.echo(f"❌ Unsupported format: {format}")
        return

    try:
        # Read input file(s)
        if format in ["ovhcloud", "hetzner"]:
            # For bare metal providers, input is API response JSON
            content = input_path.read_text()
            click.echo(f"🔄 Parsing {format} API response...")
            infra = parser.parse_from_api_response(content)
        elif input_path.is_dir():
            # Handle directory input (for Kubernetes manifests)
            content = ""
            for file_path in input_path.glob("*.yaml"):
                content += file_path.read_text() + "\n---\n"
            for file_path in input_path.glob("*.yml"):
                content += file_path.read_text() + "\n---\n"
            click.echo(f"🔄 Parsing {format} infrastructure...")
            infra = parser.parse(content)
        else:
            content = input_path.read_text()
            click.echo(f"🔄 Parsing {format} infrastructure...")
            infra = parser.parse(content)

        # Convert to dict for YAML output
        infra_dict = {
            "name": infra.name,
            "description": infra.description,
            "service_type": infra.service_type,
            "provider": infra.provider.value,
            "region": infra.region,
            "environment": infra.environment,
        }

        if infra.bare_metal:
            infra_dict["bare_metal"] = {
                "server_model": infra.bare_metal.server_model,
                "cpu_cores": infra.bare_metal.cpu_cores,
                "ram_gb": infra.bare_metal.ram_gb,
                "storage_type": infra.bare_metal.storage_type,
                "storage_gb": infra.bare_metal.storage_gb,
                "os": infra.bare_metal.os,
                "ssh_keys": infra.bare_metal.ssh_keys,
            }

        if infra.compute:
            infra_dict["compute"] = {
                "instances": infra.compute.instances,
                "cpu": infra.compute.cpu,
                "memory": infra.compute.memory,
                "disk": infra.compute.disk,
                "auto_scale": infra.compute.auto_scale,
                "min_instances": infra.compute.min_instances,
                "max_instances": infra.compute.max_instances,
                "cpu_target": infra.compute.cpu_target,
                "memory_target": infra.compute.memory_target,
            }

        if infra.container:
            infra_dict["container"] = {
                "image": infra.container.image,
                "tag": infra.container.tag,
                "port": infra.container.port,
                "environment": infra.container.environment,
                "secrets": infra.container.secrets,
                "cpu_limit": infra.container.cpu_limit,
                "memory_limit": infra.container.memory_limit,
                "cpu_request": infra.container.cpu_request,
                "memory_request": infra.container.memory_request,
                "health_check_path": infra.container.health_check_path,
            }

        if infra.database:
            infra_dict["database"] = {
                "type": infra.database.type.value,
                "version": infra.database.version,
                "storage": infra.database.storage,
                "multi_az": infra.database.multi_az,
                "replicas": infra.database.replicas,
                "backup_enabled": infra.database.backup_enabled,
                "backup_retention_days": infra.database.backup_retention_days,
                "encryption_at_rest": infra.database.encryption_at_rest,
                "encryption_in_transit": infra.database.encryption_in_transit,
                "publicly_accessible": infra.database.publicly_accessible,
            }

        if infra.network:
            infra_dict["network"] = {
                "vpc_cidr": infra.network.vpc_cidr,
                "public_subnets": infra.network.public_subnets,
                "private_subnets": infra.network.private_subnets,
                "enable_nat_gateway": infra.network.enable_nat_gateway,
                "enable_vpn_gateway": infra.network.enable_vpn_gateway,
            }

        if infra.load_balancer:
            infra_dict["load_balancer"] = {
                "enabled": infra.load_balancer.enabled,
                "type": infra.load_balancer.type,
                "https": infra.load_balancer.https,
                "certificate_domain": infra.load_balancer.certificate_domain,
                "health_check_path": infra.load_balancer.health_check_path,
                "sticky_sessions": infra.load_balancer.sticky_sessions,
            }

        if infra.volumes:
            infra_dict["volumes"] = [
                {
                    "name": vol.name,
                    "size": vol.size,
                    "mount_path": vol.mount_path,
                    "storage_class": vol.storage_class,
                }
                for vol in infra.volumes
            ]

        if infra.security.secrets:
            infra_dict.setdefault("security", {})["secrets"] = infra.security.secrets

        if infra.tags:
            infra_dict["tags"] = infra.tags

        # Determine output file
        if output:
            output_path = Path(output)
        else:
            output_path = input_path.with_suffix('.infra.yaml')

        # Write YAML output
        with open(output_path, 'w') as f:
            yaml.dump(infra_dict, f, default_flow_style=False, sort_keys=False)

        click.echo(f"✅ Infrastructure reverse engineered to {output_path}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        return 1


@infrastructure.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--platform", "-p", type=click.Choice(["terraform-aws", "terraform-gcp", "terraform-azure", "cloudformation", "pulumi", "kubernetes", "ovhcloud", "hetzner"]), default="terraform-aws", help="Target platform")
@click.option("--output", "-o", type=click.Path(), help="Output file/directory")
def generate_infra(input_file, platform, output):
    """
    Generate infrastructure from universal format

    Examples:
        specql infrastructure generate-infra infra.yaml
        specql infrastructure generate-infra infra.yaml -p kubernetes -o k8s/
        specql infrastructure generate-infra infra.yaml -p terraform-aws -o terraform/
    """
    input_path = Path(input_file)

    try:
        # Read and parse YAML
        with open(input_path) as f:
            infra_dict = yaml.safe_load(f)

        # Convert to UniversalInfrastructure
        infra = UniversalInfrastructure(
            name=infra_dict["name"],
            description=infra_dict.get("description", ""),
            service_type=infra_dict.get("service_type", "api"),
            provider=CloudProvider(infra_dict.get("provider", "aws")),
            region=infra_dict.get("region", "us-east-1"),
            environment=infra_dict.get("environment", "production"),
        )

        # Add compute config
        if "compute" in infra_dict:
            compute_dict = infra_dict["compute"]
            from src.infrastructure.universal_infra_schema import ComputeConfig
            infra.compute = ComputeConfig(
                instances=compute_dict.get("instances", 1),
                cpu=compute_dict.get("cpu", 1.0),
                memory=compute_dict.get("memory", "2GB"),
                disk=compute_dict.get("disk", "20GB"),
                auto_scale=compute_dict.get("auto_scale", False),
                min_instances=compute_dict.get("min_instances", 1),
                max_instances=compute_dict.get("max_instances", 10),
                cpu_target=compute_dict.get("cpu_target", 70),
                memory_target=compute_dict.get("memory_target", 80),
            )

        # Add container config
        if "container" in infra_dict:
            container_dict = infra_dict["container"]
            from src.infrastructure.universal_infra_schema import ContainerConfig
            infra.container = ContainerConfig(
                image=container_dict["image"],
                tag=container_dict.get("tag", "latest"),
                port=container_dict.get("port", 8000),
                environment=container_dict.get("environment", {}),
                secrets=container_dict.get("secrets", {}),
                cpu_limit=container_dict.get("cpu_limit"),
                memory_limit=container_dict.get("memory_limit"),
                cpu_request=container_dict.get("cpu_request"),
                memory_request=container_dict.get("memory_request"),
                health_check_path=container_dict.get("health_check_path", "/health"),
            )

        # Add database config
        if "database" in infra_dict:
            db_dict = infra_dict["database"]
            from src.infrastructure.universal_infra_schema import DatabaseConfig, DatabaseType
            infra.database = DatabaseConfig(
                type=DatabaseType(db_dict["type"]),
                version=db_dict.get("version", "15"),
                storage=db_dict.get("storage", "50GB"),
                multi_az=db_dict.get("multi_az", False),
                replicas=db_dict.get("replicas", 0),
                backup_enabled=db_dict.get("backup_enabled", True),
                backup_retention_days=db_dict.get("backup_retention_days", 7),
                encryption_at_rest=db_dict.get("encryption_at_rest", True),
                encryption_in_transit=db_dict.get("encryption_in_transit", True),
                publicly_accessible=db_dict.get("publicly_accessible", False),
            )

        # Add network config
        if "network" in infra_dict:
            network_dict = infra_dict["network"]
            from src.infrastructure.universal_infra_schema import NetworkConfig
            infra.network = NetworkConfig(
                vpc_cidr=network_dict.get("vpc_cidr", "10.0.0.0/16"),
                public_subnets=network_dict.get("public_subnets", ["10.0.1.0/24", "10.0.2.0/24"]),
                private_subnets=network_dict.get("private_subnets", ["10.0.10.0/24", "10.0.20.0/24"]),
                enable_nat_gateway=network_dict.get("enable_nat_gateway", True),
                enable_vpn_gateway=network_dict.get("enable_vpn_gateway", False),
            )

        # Add load balancer config
        if "load_balancer" in infra_dict:
            lb_dict = infra_dict["load_balancer"]
            from src.infrastructure.universal_infra_schema import LoadBalancerConfig
            infra.load_balancer = LoadBalancerConfig(
                enabled=lb_dict.get("enabled", True),
                type=lb_dict.get("type", "application"),
                https=lb_dict.get("https", True),
                certificate_domain=lb_dict.get("certificate_domain"),
                health_check_path=lb_dict.get("health_check_path", "/health"),
                sticky_sessions=lb_dict.get("sticky_sessions", False),
            )

        # Add volumes
        if "volumes" in infra_dict:
            from src.infrastructure.universal_infra_schema import Volume
            infra.volumes = [
                Volume(
                    name=vol["name"],
                    size=vol.get("size", "10GB"),
                    mount_path=vol.get("mount_path", "/data"),
                    storage_class=vol.get("storage_class", "standard"),
                )
                for vol in infra_dict["volumes"]
            ]

        # Add security config
        if "security" in infra_dict and "secrets" in infra_dict["security"]:
            from src.infrastructure.universal_infra_schema import SecurityConfig
            infra.security = SecurityConfig(secrets=infra_dict["security"]["secrets"])

        # Add tags
        if "tags" in infra_dict:
            infra.tags = infra_dict["tags"]

        # Add bare metal config
        if "bare_metal" in infra_dict:
            bm_dict = infra_dict["bare_metal"]
            from src.infrastructure.universal_infra_schema import BareMetalConfig
            infra.bare_metal = BareMetalConfig(
                server_model=bm_dict.get("server_model", ""),
                cpu_cores=bm_dict.get("cpu_cores", 2),
                ram_gb=bm_dict.get("ram_gb", 4),
                storage_type=bm_dict.get("storage_type", "ssd"),
                storage_gb=bm_dict.get("storage_gb", 40),
                os=bm_dict.get("os", "ubuntu2204"),
                ssh_keys=bm_dict.get("ssh_keys", []),
                private_network=bm_dict.get("private_network", False),
                ipv6=bm_dict.get("ipv6", False),
                backup_service=bm_dict.get("backup_service", False),
                monitoring=bm_dict.get("monitoring", False),
                datacenter=bm_dict.get("datacenter"),
                bandwidth=bm_dict.get("bandwidth"),
            )

        # Select generator based on platform
        if platform == "terraform-aws":
            generator = TerraformAWSGenerator()
            output_content = infra.to_terraform_aws()
            output_ext = ".tf"
        elif platform == "terraform-gcp":
            generator = TerraformGCPGenerator()
            output_content = infra.to_terraform_gcp()
            output_ext = ".tf"
        elif platform == "terraform-azure":
            generator = TerraformAzureGenerator()
            output_content = infra.to_terraform_azure()
            output_ext = ".tf"
        elif platform == "cloudformation":
            generator = CloudFormationGenerator()
            output_content = generator.generate(infra)
            output_ext = ".json"
        elif platform == "pulumi":
            generator = PulumiGenerator()
            output_content = generator.generate(infra)
            output_ext = ".py"
        elif platform == "kubernetes":
            generator = KubernetesGenerator()
            output_content = infra.to_kubernetes()
            output_ext = ".yaml"
        elif platform == "ovhcloud":
            generator = OVHcloudGenerator()
            output_content = infra.to_ovhcloud()
            output_ext = ".sh"
        elif platform == "hetzner":
            generator = HetznerGenerator()
            output_content = infra.to_hetzner()
            output_ext = ".sh"
        else:
            click.echo(f"❌ Unsupported platform: {platform}")
            return 1

        # Determine output file
        if output:
            output_path = Path(output)
            if output_path.is_dir():
                output_path = output_path / f"{infra.name}{output_ext}"
        else:
            output_path = input_path.with_suffix(output_ext)

        # Write output
        with open(output_path, 'w') as f:
            f.write(output_content)

        click.echo(f"✅ Infrastructure generated for {platform} at {output_path}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        return 1


@infrastructure.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--from-platform", "from_platform", type=click.Choice(["terraform", "kubernetes", "docker-compose"]), help="Source platform")
@click.option("--to-platform", "to_platform", type=click.Choice(["terraform-aws", "terraform-gcp", "terraform-azure", "cloudformation", "pulumi", "kubernetes"]), help="Target platform")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def convert(input_file, from_platform, to_platform, output):
    """
    Convert infrastructure between platforms

    Examples:
        specql infrastructure convert infra.yaml --from terraform --to kubernetes
        specql infrastructure convert docker-compose.yml --from docker-compose --to terraform-aws
    """
    if not from_platform or not to_platform:
        click.echo("❌ Must specify both --from-platform and --to-platform")
        return 1

    # First reverse engineer
    click.echo(f"🔄 Converting from {from_platform} to {to_platform}...")

    # Create a temporary file for the intermediate YAML
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as temp_file:
        temp_yaml = temp_file.name

    # Step 1: Reverse engineer to universal format
    try:
        reverse_infra.callback(input_file, temp_yaml, from_platform)
    except Exception as e:
        click.echo(f"❌ Reverse engineering failed: {e}")
        Path(temp_yaml).unlink(missing_ok=True)
        return 1

    # Step 2: Generate to target platform
    try:
        generate_infra.callback(temp_yaml, to_platform, output)
    except Exception as e:
        click.echo(f"❌ Generation failed: {e}")
        Path(temp_yaml).unlink(missing_ok=True)
        return 1
    finally:
        # Clean up temporary file
        Path(temp_yaml).unlink(missing_ok=True)

    click.echo(f"✅ Conversion complete: {from_platform} → {to_platform}")


@infrastructure.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--provider", "-p", type=click.Choice(["aws", "gcp", "azure", "ovhcloud", "hetzner"]), help="Cloud provider for cost estimation")
@click.option("--format", type=click.Choice(["json", "table"]), default="table", help="Output format")
def estimate_cost(input_file, provider, format):
    """
    Estimate monthly infrastructure costs

    Examples:
        specql infrastructure estimate-cost infra.yaml
        specql infrastructure estimate-cost infra.yaml -p aws --format json
        specql infrastructure estimate-cost infra.yaml --format table
    """
    input_path = Path(input_file)

    try:
        # Read and parse YAML
        with open(input_path) as f:
            infra_dict = yaml.safe_load(f)

        # Convert to UniversalInfrastructure
        infra = UniversalInfrastructure(
            name=infra_dict["name"],
            description=infra_dict.get("description", ""),
            service_type=infra_dict.get("service_type", "api"),
            provider=CloudProvider(infra_dict.get("provider", "aws")),
            region=infra_dict.get("region", "us-east-1"),
            environment=infra_dict.get("environment", "production"),
        )

        # Add compute config
        if "compute" in infra_dict:
            compute_dict = infra_dict["compute"]
            from src.infrastructure.universal_infra_schema import ComputeConfig
            infra.compute = ComputeConfig(
                instances=compute_dict.get("instances", 1),
                cpu=compute_dict.get("cpu", 1.0),
                memory=compute_dict.get("memory", "2GB"),
                disk=compute_dict.get("disk", "20GB"),
                auto_scale=compute_dict.get("auto_scale", False),
                min_instances=compute_dict.get("min_instances", 1),
                max_instances=compute_dict.get("max_instances", 10),
                cpu_target=compute_dict.get("cpu_target", 70),
                memory_target=compute_dict.get("memory_target", 80),
            )

        # Add database config
        if "database" in infra_dict:
            db_dict = infra_dict["database"]
            from src.infrastructure.universal_infra_schema import DatabaseConfig, DatabaseType
            infra.database = DatabaseConfig(
                type=DatabaseType(db_dict["type"]),
                version=db_dict.get("version", "15"),
                storage=db_dict.get("storage", "50GB"),
                multi_az=db_dict.get("multi_az", False),
                replicas=db_dict.get("replicas", 0),
                backup_enabled=db_dict.get("backup_enabled", True),
                backup_retention_days=db_dict.get("backup_retention_days", 7),
                encryption_at_rest=db_dict.get("encryption_at_rest", True),
                encryption_in_transit=db_dict.get("encryption_in_transit", True),
                publicly_accessible=db_dict.get("publicly_accessible", False),
            )

        # Add load balancer config
        if "load_balancer" in infra_dict:
            lb_dict = infra_dict["load_balancer"]
            from src.infrastructure.universal_infra_schema import LoadBalancerConfig
            infra.load_balancer = LoadBalancerConfig(
                enabled=lb_dict.get("enabled", True),
                type=lb_dict.get("type", "application"),
                https=lb_dict.get("https", True),
                certificate_domain=lb_dict.get("certificate_domain"),
                health_check_path=lb_dict.get("health_check_path", "/health"),
                sticky_sessions=lb_dict.get("sticky_sessions", False),
            )

        # Add volumes
        if "volumes" in infra_dict:
            from src.infrastructure.universal_infra_schema import Volume
            infra.volumes = [
                Volume(
                    name=vol["name"],
                    size=vol.get("size", "10GB"),
                    mount_path=vol.get("mount_path", "/data"),
                    storage_class=vol.get("storage_class", "standard"),
                )
                for vol in infra_dict["volumes"]
            ]

        # Add bare metal config
        if "bare_metal" in infra_dict:
            bm_dict = infra_dict["bare_metal"]
            from src.infrastructure.universal_infra_schema import BareMetalConfig
            infra.bare_metal = BareMetalConfig(
                server_model=bm_dict.get("server_model", ""),
                cpu_cores=bm_dict.get("cpu_cores", 4),
                ram_gb=bm_dict.get("ram_gb", 16),
                storage_type=bm_dict.get("storage_type", "ssd"),
                storage_gb=bm_dict.get("storage_gb", 80),
                os=bm_dict.get("os", "ubuntu2204"),
                ssh_keys=bm_dict.get("ssh_keys", []),
            )

        # Estimate costs
        if provider:
            # Single provider estimate
            infra.provider = CloudProvider(provider)
            cost_breakdown = infra.estimate_cost()

            if format == "json":
                import json
                click.echo(json.dumps(cost_breakdown.to_dict(), indent=2))
            else:
                click.echo(f"💰 Cost Estimate for {provider.upper()}")
                click.echo(f"Compute:        ${cost_breakdown.compute_cost:.2f}/month")
                click.echo(f"Database:       ${cost_breakdown.database_cost:.2f}/month")
                click.echo(f"Storage:        ${cost_breakdown.storage_cost:.2f}/month")
                click.echo(f"Network:        ${cost_breakdown.network_cost:.2f}/month")
                click.echo(f"Load Balancer:  ${cost_breakdown.load_balancer_cost:.2f}/month")
                click.echo(f"Monitoring:     ${cost_breakdown.monitoring_cost:.2f}/month")
                click.echo("-" * 50)
                click.echo(f"Total:          ${cost_breakdown.total_monthly_cost:.2f}/month")
        else:
            # Cost comparison across all providers
            comparisons = infra.get_cost_comparison()

            if format == "json":
                import json
                result = {}
                for provider_name, breakdown in comparisons.items():
                    result[provider_name] = breakdown.to_dict()
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo("💰 Cost Comparison Across Cloud Providers")
                click.echo("-" * 60)

                # Header
                click.echo("<15")
                click.echo("-" * 60)

                # Data rows
                for provider_name, breakdown in comparisons.items():
                    click.echo("<15")

                click.echo("-" * 60)
                click.echo("Note: Estimates are approximate and based on on-demand pricing.")

    except Exception as e:
        click.echo(f"❌ Error estimating costs: {e}")
        return 1


if __name__ == "__main__":
    infrastructure()