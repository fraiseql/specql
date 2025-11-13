"""Tests for Docker Compose → Universal Infrastructure parser"""

import pytest
from src.infrastructure.parsers.docker_compose_parser import DockerComposeParser
from src.infrastructure.universal_infra_schema import *


class TestDockerComposeParser:
    """Test parsing Docker Compose to universal format"""

    @pytest.fixture
    def parser(self):
        return DockerComposeParser()

    def test_parse_simple_web_app(self, parser):
        """Test parsing basic web app with database"""
        compose_content = """
version: '3.8'
services:
  web:
    image: nginx:1.21
    ports:
      - "80:80"
    environment:
      - ENV=production
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""

        # Act
        infra = parser.parse(compose_content)

        # Assert
        assert infra.name == "web"
        assert infra.provider == CloudProvider.DOCKER

        # Container
        assert infra.container is not None
        assert infra.container.image == "nginx:1.21"
        assert infra.container.port == 80
        assert infra.container.environment == {"ENV": "production"}
        assert infra.container.cpu_limit == 1.0
        assert infra.container.memory_limit == "512MB"
        assert infra.container.cpu_request == 0.5
        assert infra.container.memory_request == "256MB"
        assert infra.container.health_check_path == "/health"

        # Database
        assert infra.database is not None
        assert infra.database.type == DatabaseType.POSTGRESQL
        assert infra.database.version == "15"

        # Volumes
        assert len(infra.volumes) == 1
        assert infra.volumes[0].name == "postgres_data"

    def test_parse_api_with_redis(self, parser):
        """Test parsing API with Redis cache"""
        compose_content = """
version: '3.8'
services:
  api:
    image: myapi:latest
    ports:
      - "8000:8000"
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: ${DATABASE_URL}
    secrets:
      - database_url
    depends_on:
      - redis
      - db

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: myapi
    volumes:
      - db_data:/var/lib/mysql

secrets:
  database_url:
    file: ./secrets/database_url.txt

volumes:
  db_data:
"""

        # Act
        infra = parser.parse(compose_content)

        # Assert
        assert infra.name == "api"
        assert infra.provider == CloudProvider.DOCKER

        # Container
        assert infra.container is not None
        assert infra.container.image == "myapi:latest"
        assert infra.container.port == 8000
        assert "REDIS_URL" in infra.container.environment
        assert infra.container.secrets == {"DATABASE_URL": "${secrets.database_url}"}

        # Database (should detect MySQL)
        assert infra.database is not None
        assert infra.database.type == DatabaseType.MYSQL
        assert infra.database.version == "8.0"

    def test_parse_complex_microservices(self, parser):
        """Test parsing complex microservices setup"""
        compose_content = """
version: '3.8'
services:
  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    depends_on:
      - api

  api:
    image: myapi:v2.1.0
    ports:
      - "8080:8080"
    environment:
      DB_HOST: db
      REDIS_HOST: redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 1G

  db:
    image: postgres:14.2
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:6.2
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
"""

        # Act
        infra = parser.parse(compose_content)

        # Assert
        assert infra.name == "frontend"  # Should detect frontend as main service
        assert infra.provider == CloudProvider.DOCKER

        # Container (frontend)
        assert infra.container is not None
        assert infra.container.image == "nginx:alpine"
        assert infra.container.port == 80

        # Database (should detect PostgreSQL)
        assert infra.database is not None
        assert infra.database.type == DatabaseType.POSTGRESQL
        assert infra.database.version == "14.2"

        # Volumes
        assert len(infra.volumes) == 2
        volume_names = [v.name for v in infra.volumes]
        assert "postgres_data" in volume_names
        assert "redis_data" in volume_names