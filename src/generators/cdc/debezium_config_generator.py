"""
Debezium Configuration Generator

Generates Debezium connector configurations for SpecQL outbox pattern.
"""

import json
from typing import Dict, Any


class DebeziumConfigGenerator:
    """Generates Debezium CDC connector configurations"""

    def generate_connector_config(
        self,
        database_host: str,
        database_name: str,
        database_user: str = "postgres",
        kafka_bootstrap_servers: str = "kafka:9092",
        kafka_topic_prefix: str = "specql",
    ) -> Dict[str, Any]:
        """Generate Debezium PostgreSQL connector config for outbox"""

        return {
            "name": "specql-outbox-connector",
            "config": {
                # Connector class
                "connector.class": "io.debezium.connector.postgresql.PostgresConnector",

                # Database connection
                "database.hostname": database_host,
                "database.port": "5432",
                "database.user": database_user,
                "database.password": "${DB_PASSWORD}",
                "database.dbname": database_name,
                "database.server.name": kafka_topic_prefix,

                # Tables to capture
                "table.include.list": "app.outbox",

                # Publication (PostgreSQL logical replication)
                "publication.name": "specql_outbox_publication",
                "publication.autocreate.mode": "filtered",

                # Slot
                "slot.name": "specql_outbox_slot",

                # Transforms: Outbox Event Router
                "transforms": "outbox",
                "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
                "transforms.outbox.table.field.event.id": "id",
                "transforms.outbox.table.field.event.key": "aggregate_id",
                "transforms.outbox.table.field.event.type": "event_type",
                "transforms.outbox.table.field.event.payload": "event_payload",
                "transforms.outbox.route.topic.replacement": "${kafka_topic_prefix}.events.${routedByValue}",
                "transforms.outbox.route.by.field": "aggregate_type",

                # Topic routing
                "topic.prefix": kafka_topic_prefix,

                # Performance
                "max.batch.size": "2048",
                "poll.interval.ms": "1000",

                # Schema
                "key.converter": "org.apache.kafka.connect.json.JsonConverter",
                "value.converter": "org.apache.kafka.connect.json.JsonConverter",
                "key.converter.schemas.enable": "false",
                "value.converter.schemas.enable": "false",

                # Cleanup processed events
                "transforms.outbox.table.op.invalid.behavior": "warn"
            }
        }

    def generate_docker_compose(
        self,
        database_host: str = "postgres",
        kafka_host: str = "kafka"
    ) -> str:
        """Generate docker-compose.yml for CDC stack"""

        return f"""version: '3.8'

services:
  # Zookeeper (required by Kafka)
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  # Kafka Connect with Debezium
  kafka-connect:
    image: debezium/connect:latest
    depends_on:
      - kafka
      - {database_host}
    ports:
      - "8083:8083"
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      GROUP_ID: 1
      CONFIG_STORAGE_TOPIC: connect_configs
      OFFSET_STORAGE_TOPIC: connect_offsets
      STATUS_STORAGE_TOPIC: connect_status
      KEY_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      VALUE_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      CONNECT_KEY_CONVERTER_SCHEMAS_ENABLE: "false"
      CONNECT_VALUE_CONVERTER_SCHEMAS_ENABLE: "false"

  # Kafka UI (optional, for monitoring)
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
"""

    def generate_deployment_script(self) -> str:
        """Generate script to deploy Debezium connector"""

        return """#!/bin/bash
# Deploy SpecQL Outbox Debezium Connector

set -e

KAFKA_CONNECT_URL="${KAFKA_CONNECT_URL:-http://localhost:8083}"
CONFIG_FILE="${1:-debezium-outbox-connector.json}"

echo "Deploying Debezium connector from $CONFIG_FILE..."

# Deploy connector
curl -X POST \\
  -H "Content-Type: application/json" \\
  -d @"$CONFIG_FILE" \\
  "$KAFKA_CONNECT_URL/connectors"

echo ""
echo "Connector deployed successfully!"

# Check status
echo ""
echo "Connector status:"
curl -s "$KAFKA_CONNECT_URL/connectors/specql-outbox-connector/status" | jq .
"""

    def generate_all(
        self,
        database_host: str,
        database_name: str,
        output_dir: str = "./cdc"
    ) -> Dict[str, str]:
        """Generate all CDC configuration files"""

        files = {}

        # Connector config
        connector_config = self.generate_connector_config(
            database_host, database_name
        )
        files['debezium-outbox-connector.json'] = json.dumps(
            connector_config, indent=2
        )

        # Docker Compose
        files['docker-compose.yml'] = self.generate_docker_compose(
            database_host
        )

        # Deployment script
        files['deploy-connector.sh'] = self.generate_deployment_script()

        return files