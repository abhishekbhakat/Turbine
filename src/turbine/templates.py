FARM_COMPOSE_TEMPLATE = """
version: '3'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
    restart: always

  redis:
    image: redis:latest
    ports:
      - 6379:6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 30s
      retries: 50
    restart: always

  vault:
    build:
      context: .
      dockerfile: vault.Dockerfile
    ports:
      - 8200:8200
    cap_add:
      - IPC_LOCK

  smtp:
    build:
      context: .
      dockerfile: smtp.Dockerfile
    ports:
      - 25:25

  marquez:
    image: marquezproject/marquez:latest
    depends_on:
      - postgres
    ports:
      - 5000:5000
      - 5001:5001
    volumes:
      - ./marquez.dev.yaml:/usr/src/app/marquez.dev.yaml
    command: ["--config", "/usr/src/app/marquez.dev.yaml"]

volumes:
  postgres-db-volume:

networks:
  default:
    name: airflow-network
"""

VAULT_DOCKERFILE_TEMPLATE = """
FROM vault:1.9.0

COPY vault.json /vault/config/vault.json

CMD ["vault", "server", "-config=/vault/config/vault.json"]
"""

VAULT_JSON_TEMPLATE = """
{
  "backend": {
    "file": {
      "path": "/vault/file"
    }
  },
  "listener": {
    "tcp": {
      "address": "0.0.0.0:8200",
      "tls_disable": 1
    }
  },
  "ui": true
}
"""

SMTP_DOCKERFILE_TEMPLATE = """
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y postfix
RUN postconf -e 'inet_interfaces = all'

EXPOSE 25

CMD ["postfix", "start-fg"]
"""

MARQUEZ_DEV_YAML_TEMPLATE = """
server:
  applicationConnectors:
    - type: http
      port: 5000
  adminConnectors:
    - type: http
      port: 5001

db:
  url: jdbc:postgresql://postgres:5432/marquez
  user: marquez
  password: marquez
"""

FARM_START_SCRIPT_TEMPLATE = """#!/bin/bash
docker-compose up -d
echo "Farm is running!"
echo "Postgres is running on port 5432"
echo "Redis is running on port 6379"
echo "Vault is available at http://localhost:8200"
echo "SMTP server is running on port 25"
echo "Marquez is available at http://localhost:5000"
"""

FARM_STOP_SCRIPT_TEMPLATE = """#!/bin/bash
docker-compose down
echo "Farm has been stopped."
"""

PROJECT_DOCKER_COMPOSE_TEMPLATE = """
version: '3'
services:
  webserver:
    build: .
    image: {tgt_folder}
    restart: always
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/{redisdb}
      - AIRFLOW__CORE__FERNET_KEY=''
      - AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - AIRFLOW__API__AUTH_BACKEND=airflow.api.auth.backend.basic_auth
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    ports:
      - "{webserver_port}:8080"
    healthcheck:
      test: ["CMD-SHELL", "[ -f /opt/airflow/airflow-webserver.pid ]"]
      interval: 30s
      timeout: 30s
      retries: 3
    networks:
      - airflow-network

  scheduler:
    build: .
    image: {tgt_folder}
    restart: always
    depends_on:
      - webserver
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/{redisdb}
      - AIRFLOW__CORE__FERNET_KEY=''
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    networks:
      - airflow-network

  worker:
    build: .
    image: {tgt_folder}
    restart: always
    depends_on:
      - scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/{redisdb}
      - AIRFLOW__CORE__FERNET_KEY=''
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    networks:
      - airflow-network

  flower:
    build: .
    image: {tgt_folder}
    restart: always
    depends_on:
      - scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=CeleryExecutor
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/{db_name}
      - AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/{redisdb}
      - AIRFLOW__CORE__FERNET_KEY=''
    ports:
      - "{flower_port}:5555"
    networks:
      - airflow-network

networks:
  airflow-network:
    external: true
"""

PROJECT_START_SCRIPT_TEMPLATE = """#!/bin/bash
set -e

PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")
AIRFLOW_IMAGE=$PROJECT_NAME
DB_NAME={db_name}

# Create project-specific database
docker run --rm --network airflow-network postgres:13 psql -h postgres -U airflow -d airflow -c "CREATE DATABASE $DB_NAME;"

# Create Airflow user
docker run --rm --network airflow-network --entrypoint airflow \
    "$AIRFLOW_IMAGE" \
    users create \
    --username admin \
    --firstname FIRST_NAME \
    --lastname LAST_NAME \
    --role Admin \
    --email admin@example.com \
    --password admin

# Initialize the database
docker run --rm --network airflow-network --entrypoint airflow \
    -e AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow:airflow@postgres/$DB_NAME" \
    "$AIRFLOW_IMAGE" \
    db init

# Start the services
docker-compose up -d

echo "Airflow project {tgt_folder} is running!"
echo "Webserver will be available at http://localhost:{webserver_port}"
echo "Flower will be available at http://localhost:{flower_port}"
"""

PROJECT_STOP_SCRIPT_TEMPLATE = """#!/bin/bash
docker-compose down
echo "Airflow project {tgt_folder} has been stopped."
"""
