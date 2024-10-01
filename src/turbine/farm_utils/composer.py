import os
import json
import stat

VAULTDOCKER = """
FROM vault:1.9.0

COPY vault.json /vault/config/vault.json

CMD ["vault", "server", "-config=/vault/config/vault.json"]
"""

VAULTJSON = """
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

FARMSTART = """#!/bin/bash
docker-compose up -d
echo "Farm is running!"
echo "Vault will be available at http://localhost:8200"
echo "Marquez will be available at http://localhost:5000"
echo "OpenSearch will be available at http://localhost:9200"
echo "OpenSearch Dashboards will be available at http://localhost:5601"
"""

FARMSMTPDOCKER = """
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y postfix
RUN postconf -e 'inet_interfaces = all'

EXPOSE 25

CMD ["postfix", "start-fg"]
"""

FARMCOMPOSE = """
version: '3'
services:
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

  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: marquez
      POSTGRES_PASSWORD: marquez
      POSTGRES_DB: marquez
    volumes:
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
      - postgres-data:/var/lib/postgresql/data
    command: postgres -c config_file=/etc/postgresql/postgresql.conf

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

  redis:
    build:
      context: .
      dockerfile: redis.Dockerfile
    ports:
      - 6379:6379

  opensearch:
    image: opensearchproject/opensearch:latest
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - opensearch-data:/usr/share/opensearch/data
    ports:
      - 9200:9200
      - 9600:9600

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:latest
    ports:
      - 5601:5601
    environment:
      OPENSEARCH_HOSTS: '["http://opensearch:9200"]'
    depends_on:
      - opensearch

volumes:
  postgres-data:
  opensearch-data:
"""

MARQUEZCONF = """
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

MARQUEZPOSTGRESCONF = """
listen_addresses = '*'
max_connections = 100
shared_buffers = 128MB
dynamic_shared_memory_type = posix
max_wal_size = 1GB
min_wal_size = 80MB
log_timezone = 'UTC'
datestyle = 'iso, mdy'
timezone = 'UTC'
lc_messages = 'en_US.utf8'
lc_monetary = 'en_US.utf8'
lc_numeric = 'en_US.utf8'
lc_time = 'en_US.utf8'
default_text_search_config = 'pg_catalog.english'
"""

REDISDOCKERFILE = """
FROM redis:latest
RUN mkdir /usr/local/etc/redis
RUN echo "databases 1000" >> /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]
"""

def get_or_create_farm():
    farm = "farm"
    if not os.path.exists(farm):
        print(f"Creating new farm...")
        os.makedirs(farm)
        os.makedirs(os.path.join(farm, "backups-s3"))
        os.makedirs(os.path.join(farm, "backups-gcs"))
        os.makedirs(os.path.join(farm, "backups-azure"))
        write_farm(farm)
        print(f"New farm created using network as 172.27.0.1/16!")
    else:
        print(f"Updating farm...")
        write_farm(farm)
        print(f"Updated farm using network as 172.27.0.1/16!")

def write_farm(farm):
    with open(os.path.join(farm, "vault.Dockerfile"), "w") as f:
        f.write(VAULTDOCKER)
    with open(os.path.join(farm, "vault.json"), "w") as f:
        f.write(VAULTJSON)
    with open(os.path.join(farm, "start.sh"), "w") as f:
        f.write(FARMSTART)
    with open(os.path.join(farm, "smtp.Dockerfile"), "w") as f:
        f.write(FARMSMTPDOCKER)
    with open(os.path.join(farm, "docker-compose.yaml"), "w") as f:
        f.write(FARMCOMPOSE)
    with open(os.path.join(farm, "marquez.dev.yaml"), "w") as f:
        f.write(MARQUEZCONF)
    with open(os.path.join(farm, "postgresql.conf"), "w") as f:
        f.write(MARQUEZPOSTGRESCONF)
    with open(os.path.join(farm, "redis.Dockerfile"), "w") as f:
        f.write(REDISDOCKERFILE)
    os.chmod(os.path.join(farm, "start.sh"), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    print(f"Farm files created in {farm} directory.")