"""
Tests for DebeziumConfigGenerator
"""

from src.generators.cdc.debezium_config_generator import DebeziumConfigGenerator


class TestDebeziumConfigGenerator:
    """Test Debezium configuration generation"""

    def test_generate_connector_config(self):
        """Test Debezium connector config generation"""
        generator = DebeziumConfigGenerator()
        config = generator.generate_connector_config(
            database_host="localhost",
            database_name="specql_db"
        )

        assert config['name'] == 'specql-outbox-connector'
        assert config['config']['table.include.list'] == 'app.outbox'
        assert config['config']['transforms'] == 'outbox'
        assert 'database.hostname' in config['config']
        assert 'database.dbname' in config['config']

    def test_generate_docker_compose(self):
        """Test docker-compose generation"""
        generator = DebeziumConfigGenerator()
        compose = generator.generate_docker_compose()

        assert 'zookeeper:' in compose
        assert 'kafka:' in compose
        assert 'kafka-connect:' in compose
        assert 'kafka-ui:' in compose

    def test_generate_deployment_script(self):
        """Test deployment script generation"""
        generator = DebeziumConfigGenerator()
        script = generator.generate_deployment_script()

        assert '#!/bin/bash' in script
        assert 'curl -X POST' in script
        assert 'specql-outbox-connector' in script

    def test_generate_all(self):
        """Test complete configuration generation"""
        generator = DebeziumConfigGenerator()
        files = generator.generate_all("localhost", "specql_db")

        assert 'debezium-outbox-connector.json' in files
        assert 'docker-compose.yml' in files
        assert 'deploy-connector.sh' in files

        # Check JSON is valid
        import json
        config = json.loads(files['debezium-outbox-connector.json'])
        assert config['name'] == 'specql-outbox-connector'