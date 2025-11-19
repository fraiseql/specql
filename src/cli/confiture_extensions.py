#!/usr/bin/env python3
"""
SpecQL Confiture Extensions
Extend Confiture CLI with SpecQL-specific commands
"""

from pathlib import Path

import click

from src.cli.orchestrator import CLIOrchestrator
from src.infrastructure.security_pattern_library import SecurityPatternLibrary


@click.group()
def specql():
    """SpecQL commands for Confiture"""
    pass


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option("--env", default="local", help="Confiture environment to use")
def generate(entity_files, foundation_only, include_tv, env):
    """Generate PostgreSQL schema from SpecQL YAML files"""

    # Create orchestrator (always use Confiture-compatible output now)
    orchestrator = CLIOrchestrator(use_registry=False, output_format="confiture")

    # Generate to db/schema/ (Confiture's expected location)
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir="db/schema",  # Changed from "migrations"
        foundation_only=foundation_only,
        include_tv=include_tv,
    )

    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red")
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    # Success - now build with Confiture
    click.secho(f"✅ Generated {len(result.migrations)} schema file(s)", fg="green")

    if not foundation_only:
        click.echo("\nBuilding final migration with Confiture...")

        # Import Confiture here to avoid circular imports
        try:
            from confiture.core.builder import SchemaBuilder  # type: ignore

            builder = SchemaBuilder(env=env)
            builder.build()  # Let Confiture use its default output path

            output_path = Path(f"db/generated/schema_{env}.sql")
            click.secho(f"✅ Complete! Migration written to: {output_path}", fg="green", bold=True)
            click.echo("\nNext steps:")
            click.echo(f"  1. Review: cat {output_path}")
            click.echo(f"  2. Apply: confiture migrate up --env {env}")
            click.echo("  3. Status: confiture migrate status")

        except ImportError:
            click.secho("⚠️  Confiture not available, generated schema files only", fg="yellow")
            click.echo("Install confiture: uv add fraiseql-confiture")
        except Exception as e:
            click.secho(f"❌ Confiture build failed: {e}", fg="red")
            return 1

    return 0


@specql.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--check-impacts", is_flag=True, help="Validate impact declarations")
@click.option("--verbose", "-v", is_flag=True)
def validate(entity_files, check_impacts, verbose):
    """Validate SpecQL entity files"""
    # Reuse existing validate.py logic by running it as a subprocess
    import subprocess
    import sys

    cmd = [sys.executable, "-m", "src.cli.validate"] + list(entity_files)
    if check_impacts:
        cmd.append("--check-impacts")
    if verbose:
        cmd.append("--verbose")

    result = subprocess.run(cmd)
    return result.returncode


# Import reverse engineering commands
from .reverse import reverse as reverse_sql_cmd
from .reverse_python import reverse_python
from .cache_commands import cache
from .detect_patterns import detect_patterns
# from .reverse_rust import reverse_rust  # TODO: Implement
# from .reverse_typescript import reverse_typescript  # TODO: Implement
# from .reverse_java import reverse_java  # TODO: Implement


@click.command()
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--framework", type=str, help="Framework to use (auto-detected if not specified)")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option("--preview", is_flag=True, help="Preview mode - do not write files")
@click.option("--with-patterns", is_flag=True, help="Auto-detect and apply architectural patterns")
@click.option("--exclude", multiple=True, help="Exclude file patterns (e.g., */tests/*)")
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.option("--clear-cache", is_flag=True, help="Clear cache before processing")
@click.option(
    "--incremental", is_flag=True, help="Only process changed files (requires previous run)"
)
@click.option("--validate", is_flag=True, help="Validate generated YAML against SpecQL schema")
@click.option("--keep-invalid", is_flag=True, help="Keep invalid output files")
@click.option("--fail-fast", is_flag=True, help="Stop processing on first error")
@click.option("--verbose", "-v", is_flag=True, help="Verbose error output with detailed logging")
def reverse(
    input_files,
    framework,
    output_dir,
    preview,
    with_patterns,
    exclude,
    no_cache,
    clear_cache,
    incremental,
    validate,
    keep_invalid,
    fail_fast,
    verbose,
):
    """
    Reverse engineer source code to SpecQL YAML format.

    SpecQL reverse engineering converts existing codebases into lightweight
    business domain YAML definitions. Supports multiple languages and frameworks
    with automatic pattern detection.

    \b
    Supported Languages & Frameworks:
      • Rust: Diesel, SeaORM
      • TypeScript: Prisma, TypeORM
      • Python: SQLAlchemy, Django, Pydantic
      • Java: JPA, Hibernate
      • SQL: PL/pgSQL functions

    \b
    Examples:
      # Auto-detect and reverse engineer a single file
      specql reverse src/models/contact.rs

      # Reverse engineer entire project with pattern detection
      specql reverse /path/to/rust/project --framework diesel --with-patterns

      # Preview what would be generated
      specql reverse models.rs --preview

      # Incremental update (only process changed files)
      specql reverse src/ --incremental --output-dir entities/

      # Validate output and fail on errors
      specql reverse src/ --validate --fail-fast

    \b
    Pattern Detection:
      When --with-patterns is enabled, SpecQL automatically detects and applies:
        • Soft Delete (deleted_at timestamps)
        • Audit Trail (created_at, updated_at tracking)
        • Multi-Tenant (tenant_id isolation)
        • State Machine (status transitions)
        • Hierarchical (parent-child relationships)
        • And 5+ more patterns...

    \b
    Performance Optimization:
      • Caching: Results are cached based on file content hash
      • Incremental: Only process files that have changed
      • Parallel: Process multiple files concurrently (coming soon)

    \b
    Output:
      Generated YAML files follow SpecQL format and can be used directly
      with 'specql generate' to produce PostgreSQL schema + GraphQL API.
    """
    from click import Context
    from pathlib import Path
    from .cache_manager import CacheManager

    if clear_cache:
        CacheManager().clear_cache()
        click.echo("✓ Cache cleared")
        return

    use_cache = not no_cache

    # Check if any input is a directory (project mode)
    has_directory = any(Path(f).is_dir() for f in input_files)

    if has_directory:
        # Project mode - use the new project processing logic
        if len(input_files) != 1:
            click.echo("❌ Project mode requires exactly one directory input")
            return

        project_path = input_files[0]
        from .reverse_common import ReverseEngineeringCLI

        ReverseEngineeringCLI.process_project(
            project_path,
            framework=framework,
            with_patterns=with_patterns,
            output_dir=str(output_dir) if output_dir else "entities/",
            exclude=list(exclude) if exclude else None,
            preview=preview,
            use_cache=use_cache,
            incremental=incremental,
            validate_output=validate,
            keep_invalid=keep_invalid,
            fail_fast=fail_fast,
            verbose=verbose,
        )
        return

    # File mode - process individual files
    for file_path in input_files:
        if not framework:
            # Simple extension-based detection
            ext = Path(file_path).suffix.lower()
            if ext == ".py":
                detected = "python"
            elif ext == ".sql":
                detected = "sql"
            elif ext == ".rs":
                detected = "rust"
            elif ext in [".ts", ".tsx"]:
                detected = "typescript"
            elif ext == ".java":
                detected = "java"
            else:
                detected = None

            if detected:
                click.echo(f"🔍 Detected language: {detected}")
                framework = detected
            else:
                click.echo(f"❌ Could not detect language for {file_path}")
                continue

        # Dispatch to appropriate parser
        if framework == "sql":
            sub_ctx = Context(reverse_sql_cmd)
            kwargs = {"sql_files": [file_path], "preview": preview}
            if output_dir is not None:
                kwargs["output_dir"] = output_dir
            sub_ctx.invoke(reverse_sql_cmd, **kwargs)
        elif framework == "python":
            sub_ctx = Context(reverse_python)
            kwargs = {
                "python_files": [file_path],
                "dry_run": preview,
                "discover_patterns": with_patterns,
            }
            if output_dir is not None:
                kwargs["output_dir"] = output_dir
            sub_ctx.invoke(reverse_python, **kwargs)
        elif framework == "rust":
            # Use the new rust reverse engineering
            from .reverse_rust import reverse_rust

            sub_ctx = Context(reverse_rust)
            kwargs = {
                "input_files": [file_path],
                "output_dir": output_dir,
                "framework": framework,
                "with_patterns": with_patterns,
                "exclude": list(exclude) if exclude else [],
                "recursive": True,
                "preview": preview,
            }
            sub_ctx.invoke(reverse_rust, **kwargs)
        elif framework == "typescript":
            click.echo(f"📘 TypeScript reverse engineering for {file_path} (not yet implemented)")
        elif framework == "java":
            click.echo(f"☕ Java reverse engineering for {file_path} (not yet implemented)")
        else:
            click.echo(f"❌ Unsupported framework: {framework}")


@click.command(name="reverse-sql")
@click.argument("sql_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option("--min-confidence", type=float, default=0.80, help="Minimum confidence threshold")
@click.option("--no-ai", is_flag=True, help="Skip AI enhancement (faster)")
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option("--compare", is_flag=True, help="Generate comparison report")
@click.option("--use-heuristics/--no-heuristics", default=True, help="Use heuristic enhancements")
def reverse_sql(sql_files, output_dir, min_confidence, no_ai, preview, compare, use_heuristics):
    """
    Reverse engineer SQL functions to SpecQL YAML

    Examples:
        specql reverse-sql function.sql
        specql reverse-sql reference_sql/**/*.sql -o entities/
        specql reverse-sql function.sql --no-ai --preview
        specql reverse-sql function.sql --min-confidence=0.90
    """
    # Import here to avoid circular imports
    from src.cli.reverse import reverse as reverse_cmd
    from click import Context

    # Create a click context and invoke the command
    ctx = Context(reverse_cmd)
    ctx.invoke(
        reverse_cmd,
        sql_files=sql_files,
        output_dir=output_dir,
        min_confidence=min_confidence,
        no_ai=no_ai,
        preview=preview,
        compare=compare,
        use_heuristics=use_heuristics,
    )


@click.command(name="reverse-python")
@click.argument("python_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="entities/",
    help="Output directory for YAML files",
)
@click.option(
    "--discover-patterns", is_flag=True, help="Discover and save patterns to pattern library"
)
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing files")
def reverse_python_cmd(python_files, output_dir, discover_patterns, dry_run):
    """
    Reverse engineer Python code (SQLAlchemy/Django) to SpecQL YAML

    Examples:
        specql reverse-python src/models/contact.py
        specql reverse-python src/models/*.py -o entities/
        specql reverse-python src/models/*.py --discover-patterns
    """
    from src.cli.reverse_python import reverse_python
    from click import Context

    ctx = Context(reverse_python)
    ctx.invoke(
        reverse_python,
        python_files=python_files,
        output_dir=output_dir,
        discover_patterns=discover_patterns,
        dry_run=dry_run,
    )


# Security pattern commands
@click.group()
def security():
    """Security pattern management commands"""
    pass


@security.command(name="list")
@click.option("--tags", multiple=True, help="Filter patterns by tags")
@click.option("--json", is_flag=True, help="Output in JSON format")
def list_patterns(tags, json):
    """List available security patterns"""
    library = SecurityPatternLibrary()
    patterns = library.list_patterns(tags=list(tags) if tags else None)

    if json:
        import json

        pattern_data = [
            {
                "name": p.name,
                "description": p.description,
                "tags": p.tags,
                "network_tiers": len(p.network_tiers),
                "has_waf": p.waf_config is not None,
                "has_vpn": p.vpn_config is not None,
                "compliance": p.compliance_preset.value if p.compliance_preset else None,
            }
            for p in patterns
        ]
        click.echo(json.dumps(pattern_data, indent=2))
        return

    if not patterns:
        click.echo("No security patterns found")
        return

    click.echo("Available Security Patterns:")
    click.echo("=" * 50)

    for pattern in patterns:
        click.echo(f"\n🔒 {pattern.name}")
        click.echo(f"   {pattern.description}")
        if pattern.tags:
            click.echo(f"   Tags: {', '.join(pattern.tags)}")
        click.echo(f"   Network tiers: {len(pattern.network_tiers)}")
        if pattern.waf_config:
            click.echo("   WAF: Enabled")
        if pattern.vpn_config:
            click.echo("   VPN: Enabled")
        if pattern.compliance_preset:
            click.echo(f"   Compliance: {pattern.compliance_preset.value}")


@security.command()
@click.argument("pattern_name")
@click.option("--json", is_flag=True, help="Output in JSON format")
def inspect(pattern_name, json):
    """Inspect a specific security pattern"""
    library = SecurityPatternLibrary()
    pattern = library.get_pattern(pattern_name)

    if not pattern:
        click.secho(f"❌ Pattern '{pattern_name}' not found", fg="red")
        available = [p.name for p in library.list_patterns()]
        click.echo(f"Available patterns: {', '.join(available)}")
        return 1

    if json:
        import json

        pattern_data = {
            "name": pattern.name,
            "description": pattern.description,
            "tags": pattern.tags,
            "network_tiers": [
                {
                    "name": tier.name,
                    "firewall_rules": [
                        {
                            "name": rule.name,
                            "protocol": rule.protocol,
                            "ports": rule.ports,
                            "source": rule.source,
                            "action": rule.action,
                        }
                        for rule in tier.firewall_rules
                    ],
                }
                for tier in pattern.network_tiers
            ],
            "waf_config": {
                "enabled": pattern.waf_config.enabled,
                "mode": pattern.waf_config.mode,
            }
            if pattern.waf_config
            else None,
            "vpn_config": {
                "enabled": pattern.vpn_config.enabled,
                "type": pattern.vpn_config.type,
            }
            if pattern.vpn_config
            else None,
            "compliance_preset": pattern.compliance_preset.value
            if pattern.compliance_preset
            else None,
        }
        click.echo(json.dumps(pattern_data, indent=2))
        return

    click.echo(f"🔍 Security Pattern: {pattern.name}")
    click.echo("=" * (20 + len(pattern.name)))
    click.echo(f"Description: {pattern.description}")
    if pattern.tags:
        click.echo(f"Tags: {', '.join(pattern.tags)}")
    if pattern.compliance_preset:
        click.echo(f"Compliance: {pattern.compliance_preset.value}")

    click.echo(f"\nNetwork Tiers ({len(pattern.network_tiers)}):")
    for tier in pattern.network_tiers:
        click.echo(f"  • {tier.name}")
        for rule in tier.firewall_rules:
            ports_str = ",".join(str(p) for p in rule.ports) if rule.ports else "all"
            click.echo(
                f"    - {rule.name}: {rule.protocol}/{ports_str} from {rule.source} ({rule.action})"
            )

    if pattern.waf_config:
        click.echo(f"\nWAF Configuration:")
        click.echo(f"  • Enabled: {pattern.waf_config.enabled}")
        click.echo(f"  • Mode: {pattern.waf_config.mode}")

    if pattern.vpn_config:
        click.echo(f"\nVPN Configuration:")
        click.echo(f"  • Enabled: {pattern.vpn_config.enabled}")
        click.echo(f"  • Type: {pattern.vpn_config.type}")


@security.command()
@click.argument("pattern_name")
@click.argument("infra_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option(
    "--platform", type=click.Choice(["aws", "gcp", "azure", "kubernetes"]), help="Target platform"
)
def apply(pattern_name, infra_file, output, platform):
    """Apply a security pattern to infrastructure configuration"""
    import yaml
    from pathlib import Path

    library = SecurityPatternLibrary()
    pattern = library.get_pattern(pattern_name)

    if not pattern:
        click.secho(f"❌ Pattern '{pattern_name}' not found", fg="red")
        available = [p.name for p in library.list_patterns()]
        click.echo(f"Available patterns: {', '.join(available)}")
        return 1

    # Load infrastructure file
    try:
        with open(infra_file, "r") as f:
            infra_data = yaml.safe_load(f)
    except Exception as e:
        click.secho(f"❌ Failed to load infrastructure file: {e}", fg="red")
        return 1

    # Apply pattern to infrastructure
    try:
        from src.infrastructure.universal_infra_schema import UniversalInfrastructure

        # Parse the infrastructure manually from dict
        # This is a simplified approach - in production you'd want proper validation
        infra = UniversalInfrastructure(
            name=infra_data.get("name", "unknown"),
            description=infra_data.get("description", ""),
            service_type=infra_data.get("service_type", "api"),
            provider=infra_data.get("provider", "aws"),
            region=infra_data.get("region", "us-east-1"),
            environment=infra_data.get("environment", "production"),
            compute=infra_data.get("compute"),
            container=infra_data.get("container"),
            database=infra_data.get("database"),
            network=infra_data.get("network", {}),
            load_balancer=infra_data.get("load_balancer"),
            cdn=infra_data.get("cdn"),
            volumes=infra_data.get("volumes", []),
            object_storage=infra_data.get("object_storage"),
            observability=infra_data.get("observability", {}),
            security=infra_data.get("security", {}),
            tags=infra_data.get("tags", {}),
        )

        # Apply the security pattern
        secured_infra = library.apply_pattern_to_infrastructure(infra, pattern_name)

        # Convert back to dict manually
        result_data = {
            "name": secured_infra.name,
            "description": secured_infra.description,
            "service_type": secured_infra.service_type,
            "provider": secured_infra.provider,
            "region": secured_infra.region,
            "environment": secured_infra.environment,
            "compute": secured_infra.compute,
            "container": secured_infra.container,
            "database": secured_infra.database,
            "network": secured_infra.network,
            "load_balancer": secured_infra.load_balancer,
            "cdn": secured_infra.cdn,
            "volumes": secured_infra.volumes,
            "object_storage": secured_infra.object_storage,
            "observability": secured_infra.observability,
            "security": secured_infra.security,
            "tags": secured_infra.tags,
        }

        # Output the result
        if output:
            with open(output, "w") as f:
                yaml.dump(result_data, f, default_flow_style=False, sort_keys=False)
            click.secho(f"✅ Security pattern applied and saved to: {output}", fg="green")
        else:
            click.echo(yaml.dump(result_data, default_flow_style=False, sort_keys=False))

    except Exception as e:
        click.secho(f"❌ Failed to apply security pattern: {e}", fg="red")
        return 1


@security.command()
@click.argument("pattern_names", nargs=-1, required=True)
@click.option("--output", "-o", type=click.Path(), help="Output composed security config to file")
@click.option("--validate", is_flag=True, help="Validate pattern compatibility")
def compose(pattern_names, output, validate):
    """Compose multiple security patterns into a single configuration"""
    library = SecurityPatternLibrary()

    if validate:
        warnings = library.validate_pattern_compatibility(list(pattern_names))
        if warnings:
            click.secho("⚠️  Pattern compatibility warnings:", fg="yellow")
            for warning in warnings:
                click.echo(f"  • {warning}")
            if not click.confirm("Continue with composition despite warnings?"):
                return 1

    try:
        composed_config = library.compose_patterns(list(pattern_names))
        config_dict = {
            "network_tiers": [
                {
                    "name": tier.name,
                    "firewall_rules": [
                        {
                            "name": rule.name,
                            "protocol": rule.protocol,
                            "ports": rule.ports,
                            "source": rule.source,
                            "action": rule.action,
                        }
                        for rule in tier.firewall_rules
                    ],
                }
                for tier in composed_config.network_tiers
            ],
            "waf": {
                "enabled": composed_config.waf.enabled,
                "mode": composed_config.waf.mode,
            }
            if composed_config.waf
            else None,
            "vpn": {
                "enabled": composed_config.vpn.enabled,
                "type": composed_config.vpn.type,
            }
            if composed_config.vpn
            else None,
            "compliance_preset": composed_config.compliance_preset.value
            if composed_config.compliance_preset
            else None,
        }

        import yaml

        if output:
            with open(output, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            click.secho(f"✅ Composed security config saved to: {output}", fg="green")
        else:
            click.echo("Composed Security Configuration:")
            click.echo("=" * 35)
            click.echo(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))

    except Exception as e:
        click.secho(f"❌ Failed to compose patterns: {e}", fg="red")
        return 1


@security.command()
@click.argument("pattern_names", nargs=-1, required=True)
def check(pattern_names):
    """Validate compatibility of security patterns"""
    library = SecurityPatternLibrary()

    warnings = library.validate_pattern_compatibility(list(pattern_names))

    if not warnings:
        click.secho("✅ All patterns are compatible", fg="green")
        return 0

    click.secho("⚠️  Compatibility issues found:", fg="yellow")
    for warning in warnings:
        click.echo(f"  • {warning}")

    return 1


@security.command()
@click.argument("pattern_name")
@click.option("--provider", type=click.Choice(["aws", "gcp", "azure", "kubernetes"]), required=True)
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--dry-run", is_flag=True, help="Show what would be generated")
def generate_infra(pattern_name, provider, output, dry_run):
    """Generate infrastructure code from security pattern"""
    library = SecurityPatternLibrary()
    pattern = library.get_pattern(pattern_name)

    if not pattern:
        click.secho(f"❌ Pattern '{pattern_name}' not found", fg="red")
        available = [p.name for p in library.list_patterns()]
        click.echo(f"Available patterns: {', '.join(available)}")
        raise SystemExit(1)

    # Convert pattern to security config
    security_config = pattern.to_security_config()

    # Generate infrastructure code based on provider
    try:
        if provider == "aws":
            from src.infrastructure.generators.aws_security_generator import AWSSecurityGenerator

            generator = AWSSecurityGenerator()
            code = generator.generate_security_groups(security_config)
        elif provider == "gcp":
            from src.infrastructure.generators.gcp_security_generator import GCPSecurityGenerator

            generator = GCPSecurityGenerator()
            code = generator.generate_firewall_rules(security_config)
        elif provider == "azure":
            from src.infrastructure.generators.azure_security_generator import (
                AzureSecurityGenerator,
            )

            generator = AzureSecurityGenerator()
            code = generator.generate_nsg_rules(security_config)
        elif provider == "kubernetes":
            from src.infrastructure.generators.kubernetes_security_generator import (
                KubernetesSecurityGenerator,
            )

            generator = KubernetesSecurityGenerator()
            code = generator.generate_network_policies(security_config)
        else:
            click.secho(f"❌ Unsupported provider: {provider}", fg="red")
            return 1

        if dry_run:
            click.echo("Generated infrastructure code:")
            click.echo("-" * 50)
            click.echo(code)
        elif output:
            Path(output).write_text(code)
            click.secho(f"✅ Generated infrastructure code to {output}", fg="green")
        else:
            click.echo(code)

        return 0

    except Exception as e:
        click.secho(f"❌ Generation failed: {e}", fg="red")
        return 1


@security.command()
@click.argument("yaml_file", type=click.Path(exists=True))
def validate_security(yaml_file):
    """Validate security configuration YAML"""
    from src.infrastructure.parsers.security_parser import SecurityPatternParser

    try:
        content = Path(yaml_file).read_text()
        parser = SecurityPatternParser()
        config = parser.parse(content)

        click.secho("✅ Valid security configuration", fg="green")
        click.echo(f"   Network tiers: {len(config.network_tiers)}")
        click.echo(f"   Firewall rules: {len(config.firewall_rules)}")
        if config.waf.enabled:
            click.echo("   WAF: Enabled")
        if config.vpn.enabled:
            click.echo("   VPN: Enabled")
        if config.compliance_preset:
            click.echo(f"   Compliance preset: {config.compliance_preset.value}")

        return 0
    except Exception as e:
        click.secho(f"❌ Validation failed: {e}", fg="red")
        raise SystemExit(1)


@security.command()
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option("--framework", type=click.Choice(["pci-dss", "hipaa", "soc2", "iso27001"]))
def check_compliance(yaml_file, framework):
    """Check compliance against security framework"""
    from src.infrastructure.parsers.security_parser import SecurityPatternParser
    from src.infrastructure.compliance.preset_manager import CompliancePresetManager
    from src.infrastructure.universal_infra_schema import CompliancePreset

    content = Path(yaml_file).read_text()
    parser = SecurityPatternParser()
    config = parser.parse(content)

    # Create infrastructure with this config
    from src.infrastructure.universal_infra_schema import UniversalInfrastructure

    infrastructure = UniversalInfrastructure(name="compliance-check", security=config)

    manager = CompliancePresetManager()

    # If framework specified, temporarily set it
    if framework:
        framework_map = {
            "pci-dss": CompliancePreset.PCI_DSS,
            "hipaa": CompliancePreset.HIPAA,
            "soc2": CompliancePreset.SOC2,
            "iso27001": CompliancePreset.ISO27001,
        }
        if framework in framework_map:
            infrastructure.security.compliance_preset = framework_map[framework]

    result = manager.validate_compliance(infrastructure)

    if result["compliant"]:
        click.secho(f"✅ Compliant with {result.get('preset', 'requirements')}", fg="green")
    else:
        click.secho("❌ Compliance gaps found:", fg="red")
        for gap in result["gaps"]:
            click.echo(f"   - {gap}")
        raise SystemExit(1)


@security.command()
@click.option(
    "--preset", type=click.Choice(["three-tier", "microservices", "api-gateway"]), required=True
)
@click.option("--compliance", type=click.Choice(["pci-dss", "hipaa", "soc2", "iso27001"]))
@click.option("--output", type=click.Path(), default="security.yaml")
def init(preset, compliance, output):
    """Initialize a new security configuration from preset"""
    library = SecurityPatternLibrary()

    # Map preset names to pattern IDs
    preset_map = {
        "three-tier": "three-tier-app",
        "microservices": "microservices",
        "api-gateway": "api-gateway",
    }

    pattern = library.get_pattern(preset_map[preset])
    if not pattern:
        click.secho(f"❌ Preset '{preset}' not found", fg="red")
        return 1

    # Generate YAML
    yaml_content = f"""# Security Configuration
# Generated from preset: {preset}
# Generated on: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

security:
"""

    if compliance:
        compliance_map = {
            "pci-dss": "pci-compliant",
            "hipaa": "hipaa",
            "soc2": "soc2",
            "iso27001": "iso27001",
        }
        yaml_content += f"  compliance_preset: {compliance_map[compliance]}\n"

    yaml_content += "\n  network_tiers:\n"

    for tier in pattern.network_tiers:
        yaml_content += f"\n    - name: {tier.name}\n"
        yaml_content += "      firewall_rules:\n"
        for rule in tier.firewall_rules:
            yaml_content += f"        - name: {rule.name}\n"
            yaml_content += f"          protocol: {rule.protocol}\n"
            yaml_content += f"          ports: {rule.ports}\n"
            yaml_content += f"          source: {rule.source}\n"

    if pattern.waf_config:
        yaml_content += "\n  waf:\n"
        yaml_content += "    enabled: true\n"
        yaml_content += f"    mode: {pattern.waf_config.mode}\n"

    if pattern.vpn_config:
        yaml_content += "\n  vpn:\n"
        yaml_content += "    enabled: true\n"
        yaml_content += f"    type: {pattern.vpn_config.type}\n"

    Path(output).write_text(yaml_content)
    click.secho(f"✅ Created security configuration: {output}", fg="green")
    click.echo("Next steps:")
    click.echo(f"  1. Edit {output} to customize your security settings")
    click.echo("  2. Validate: specql security validate {output}")
    click.echo("  3. Check compliance: specql security check-compliance {output}")
    click.echo(
        "  4. Generate infrastructure: specql security generate <pattern> --provider <aws|gcp|azure|kubernetes>"
    )


@security.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
def diff(file1, file2):
    """Compare two security configuration files"""
    from src.infrastructure.parsers.security_parser import SecurityPatternParser
    import yaml

    try:
        parser = SecurityPatternParser()

        # Parse both files
        content1 = Path(file1).read_text()
        content2 = Path(file2).read_text()

        config1 = parser.parse(content1)
        config2 = parser.parse(content2)

        # Compare configurations
        differences = []

        # Compare network tiers
        tiers1 = {tier.name: tier for tier in config1.network_tiers}
        tiers2 = {tier.name: tier for tier in config2.network_tiers}

        all_tier_names = set(tiers1.keys()) | set(tiers2.keys())

        for tier_name in sorted(all_tier_names):
            if tier_name not in tiers1:
                differences.append(f"Added network tier: {tier_name}")
            elif tier_name not in tiers2:
                differences.append(f"Removed network tier: {tier_name}")
            else:
                # Compare tier details
                tier1 = tiers1[tier_name]
                tier2 = tiers2[tier_name]

                if len(tier1.firewall_rules) != len(tier2.firewall_rules):
                    differences.append(
                        f"Firewall rules changed in {tier_name}: {len(tier1.firewall_rules)} → {len(tier2.firewall_rules)}"
                    )

        # Compare WAF
        if config1.waf.enabled != config2.waf.enabled:
            differences.append(f"WAF enabled: {config1.waf.enabled} → {config2.waf.enabled}")

        # Compare compliance presets
        preset1 = config1.compliance_preset.value if config1.compliance_preset else None
        preset2 = config2.compliance_preset.value if config2.compliance_preset else None
        if preset1 != preset2:
            differences.append(f"Compliance preset: {preset1} → {preset2}")

        if not differences:
            click.secho("✅ No differences found", fg="green")
            return 0

        click.secho("🔍 Differences found:", fg="yellow")
        for diff in differences:
            click.echo(f"  • {diff}")

        raise SystemExit(1)

    except Exception as e:
        click.secho(f"❌ Diff failed: {e}", fg="red")
        raise SystemExit(1)


# Register commands with the main specql group
specql.add_command(security)
specql.add_command(reverse)
specql.add_command(reverse_sql)
specql.add_command(reverse_python_cmd)
specql.add_command(detect_patterns)
specql.add_command(cache)


if __name__ == "__main__":
    specql()
