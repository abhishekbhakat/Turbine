import os
import stat


def get_or_create_farm():
    farm = "farm"
    if not os.path.exists(farm):
        print("Creating new farm...")
        os.makedirs(farm)
        os.makedirs(os.path.join(farm, "backups-s3"))
        os.makedirs(os.path.join(farm, "backups-gcs"))
        os.makedirs(os.path.join(farm, "backups-azure"))
        write_farm(farm)
        print("New farm created using network as 172.27.0.1/16!")
    else:
        print("Updating farm...")
        write_farm(farm)
        print("Updated farm using network as 172.27.0.1/16!")


def write_farm(farm):
    # Write docker-compose.yaml for the farm
    farm_compose_content = """
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
    with open(os.path.join(farm, "docker-compose.yaml"), "w") as f:
        f.write(farm_compose_content)

    # Write vault.Dockerfile
    vault_dockerfile_content = """
FROM vault:1.9.0

COPY vault.json /vault/config/vault.json

CMD ["vault", "server", "-config=/vault/config/vault.json"]
"""
    with open(os.path.join(farm, "vault.Dockerfile"), "w") as f:
        f.write(vault_dockerfile_content)

    # Write vault.json
    vault_json_content = """
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
    with open(os.path.join(farm, "vault.json"), "w") as f:
        f.write(vault_json_content)

    # Write smtp.Dockerfile
    smtp_dockerfile_content = """
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y postfix
RUN postconf -e 'inet_interfaces = all'

EXPOSE 25

CMD ["postfix", "start-fg"]
"""
    with open(os.path.join(farm, "smtp.Dockerfile"), "w") as f:
        f.write(smtp_dockerfile_content)

    # Write marquez.dev.yaml
    marquez_dev_yaml_content = """
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
    with open(os.path.join(farm, "marquez.dev.yaml"), "w") as f:
        f.write(marquez_dev_yaml_content)

    # Write start.sh
    start_script_content = """#!/bin/bash
docker-compose up -d
echo "Farm is running!"
echo "Postgres is running on port 5432"
echo "Redis is running on port 6379"
echo "Vault is available at http://localhost:8200"
echo "SMTP server is running on port 25"
echo "Marquez is available at http://localhost:5000"
"""
    start_script_path = os.path.join(farm, "start.sh")
    with open(start_script_path, "w") as f:
        f.write(start_script_content)
    os.chmod(start_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Write stop.sh
    stop_script_content = """#!/bin/bash
docker-compose down
echo "Farm has been stopped."
"""
    stop_script_path = os.path.join(farm, "stop.sh")
    with open(stop_script_path, "w") as f:
        f.write(stop_script_content)
    os.chmod(stop_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    print(f"Farm files created in {farm} directory.")
