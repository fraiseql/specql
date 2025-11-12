"""CLI commands for CDC/Outbox setup"""

import click
from pathlib import Path
from src.generators.cdc.debezium_config_generator import DebeziumConfigGenerator


@click.group()
def cdc():
    """CDC and event streaming commands"""
    pass


@cdc.command()
@click.option('--database-host', default='localhost', help='PostgreSQL host')
@click.option('--database-name', required=True, help='PostgreSQL database name')
@click.option('--kafka-host', default='kafka:9092', help='Kafka bootstrap servers')
@click.option('--output-dir', default='./cdc', help='Output directory')
def generate_config(database_host, database_name, kafka_host, output_dir):
    """Generate Debezium connector configuration"""

    generator = DebeziumConfigGenerator()
    files = generator.generate_all(database_host, database_name, output_dir)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        file_path = output_path / filename
        file_path.write_text(content)
        click.echo(f"Generated {file_path}")

    click.echo(f"\nCDC configuration generated in {output_dir}/")
    click.echo("\nNext steps:")
    click.echo("1. Start CDC stack: cd cdc && docker-compose up -d")
    click.echo("2. Deploy connector: ./deploy-connector.sh")
    click.echo("3. Monitor: http://localhost:8080 (Kafka UI)")


@cdc.command()
@click.option('--kafka-connect-url', default='http://localhost:8083')
def status(kafka_connect_url):
    """Check Debezium connector status"""
    import requests

    try:
        response = requests.get(f"{kafka_connect_url}/connectors/specql-outbox-connector/status")
        status = response.json()

        click.echo(f"Connector: {status['name']}")
        click.echo(f"State: {status['connector']['state']}")
        click.echo(f"Worker: {status['connector']['worker_id']}")

        for task in status.get('tasks', []):
            click.echo(f"Task {task['id']}: {task['state']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    cdc()