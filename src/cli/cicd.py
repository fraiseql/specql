"""
CI/CD Pipeline Commands for SpecQL

Commands for reverse engineering and generating CI/CD pipelines.
"""

import click
from pathlib import Path

from src.cicd.parsers.parser_factory import ParserFactory
from src.cicd.generators.github_actions_generator import GitHubActionsGenerator
from src.cicd.generators.gitlab_ci_generator import GitLabCIGenerator
from src.cicd.generators.circleci_generator import CircleCIGenerator
from src.cicd.generators.jenkins_generator import JenkinsGenerator
from src.cicd.generators.azure_generator import AzureGenerator


@click.group()
def cicd():
    """CI/CD pipeline management commands"""
    pass


@cicd.command()
@click.argument("pipeline_file", type=click.Path(exists=True))
@click.option("--platform", type=click.Choice(["github-actions", "gitlab-ci", "circleci", "jenkins", "azure"]), default="github-actions",
              help="Target CI/CD platform")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def generate_cicd(pipeline_file, platform, output):
    """
    Generate CI/CD pipeline from universal YAML

    PIPELINE_FILE: Path to universal pipeline YAML file

    Examples:
        specql generate-cicd pipeline.yaml --platform github-actions
        specql generate-cicd pipeline.yaml --platform gitlab-ci --output .gitlab-ci.yml
    """
    # TODO: Implement pipeline loading from YAML
    # For now, just show the command structure
    click.echo(f"Generating {platform} pipeline from {pipeline_file}")
    if output:
        click.echo(f"Output will be written to {output}")


@cicd.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--platform", type=click.Choice(["github-actions", "gitlab-ci", "circleci", "jenkins", "azure"]), default="auto",
              help="Source CI/CD platform (auto-detect if not specified)")
@click.option("--output", "-o", type=click.Path(), help="Output universal YAML file")
def reverse_cicd(config_file, platform, output):
    """
    Reverse engineer CI/CD config to universal format

    CONFIG_FILE: Path to existing CI/CD configuration file

    Examples:
        specql reverse-cicd .github/workflows/ci.yml
        specql reverse-cicd .gitlab-ci.yml --platform gitlab-ci
    """
    try:
        # Parse the file using the parser factory
        pipeline = ParserFactory.parse_file(Path(config_file))

        # Convert to YAML
        import yaml
        yaml_output = yaml.dump(pipeline.__dict__, default_flow_style=False)

        if output:
            Path(output).write_text(yaml_output)
            click.echo(f"Universal pipeline written to {output}")
        else:
            click.echo("Universal Pipeline YAML:")
            click.echo(yaml_output)

    except Exception as e:
        click.secho(f"Error parsing {config_file}: {e}", fg="red")
        return 1


@cicd.command()
@click.argument("universal_file", type=click.Path(exists=True))
@click.argument("target_platform", type=click.Choice(["github-actions", "gitlab-ci", "circleci", "jenkins", "azure"]))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def convert_cicd(universal_file, target_platform, output):
    """
    Convert universal pipeline to specific platform

    UNIVERSAL_FILE: Path to universal pipeline YAML
    TARGET_PLATFORM: Target CI/CD platform

    Examples:
        specql convert-cicd pipeline.yaml github-actions
        specql convert-cicd pipeline.yaml gitlab-ci --output .gitlab-ci.yml
    """
    try:
        # Load universal pipeline
        import yaml
        with open(universal_file, 'r') as f:
            data = yaml.safe_load(f)

        # Create pipeline object (simplified)
        from src.cicd.universal_pipeline_schema import UniversalPipeline
        pipeline = UniversalPipeline(**data)

        # Generate platform-specific config
        if target_platform == "github-actions":
            generator = GitHubActionsGenerator()
            result = generator.generate(pipeline)
        elif target_platform == "gitlab-ci":
            generator = GitLabCIGenerator()
            result = generator.generate(pipeline)
        elif target_platform == "circleci":
            generator = CircleCIGenerator()
            result = generator.generate(pipeline)
        elif target_platform == "jenkins":
            generator = JenkinsGenerator()
            result = generator.generate(pipeline)
        elif target_platform == "azure":
            generator = AzureGenerator()
            result = generator.generate(pipeline)

        if output:
            Path(output).write_text(result)
            click.echo(f"{target_platform} pipeline written to {output}")
        else:
            click.echo(f"{target_platform} Pipeline:")
            click.echo(result)

    except Exception as e:
        click.secho(f"Error converting {universal_file}: {e}", fg="red")
        return 1


@cicd.command()
@click.argument("patterns", nargs=-1)
@click.option("--query", "-q", help="Search query for patterns")
@click.option("--category", "-c", help="Filter by category")
def search_pipeline(patterns, query, category):
    """
    Search CI/CD pipeline patterns

    Examples:
        specql search-pipeline "fastapi backend"
        specql search-pipeline --category backend
    """
    click.echo("Pipeline pattern search not yet implemented")
    click.echo(f"Query: {query or 'N/A'}")
    click.echo(f"Category: {category or 'N/A'}")
    click.echo(f"Patterns: {patterns}")


if __name__ == "__main__":
    cicd()