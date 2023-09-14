ASTRO_DOCKERFILE = """
USER root
RUN sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg 16" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
RUN sudo apt-get -y update && sudo apt-get -y install postgresql-client patch
USER astro
ENV AIRFLOW__CORE__FERNET_KEY=hspWEGdpVbFQmUKyvlwz3y-STqB54lGM1oui4mRQupw=
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://postgres:postgres@172.22.0.1:5433/{0}
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__WEBSERVER__RBAC=True
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
ENV AIRFLOW__LOGGING__REMOTE_LOGGING={2}
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=
ENV AIRFLOW__ELASTICSEARCH__FRONTEND="http://localhost:5601/app/kibana#/discover?_a=(columns:!(message),query:(language:kuery,query:'log_id: \"{{log_id}}\"'),sort:!(log.offset,asc))"
ENV AIRFLOW__ELASTICSEARCH__HOST=admin:admin@172.22.0.1:9200
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__USE_SSL=False
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__VERIFY_CERTS=False
ENV AIRFLOW__ELASTICSEARCH__JSON_FORMAT=False
ENV AIRFLOW__ELASTICSEARCH__HOST_FIELD=host.name
ENV AIRFLOW__ELASTICSEARCH__OFFSET_FIELD=offset
ENV AIRFLOW__ELASTICSEARCH__LOG_ID_TEMPLATE='{{dag_id}}-{{task_id}}-{{run_id}}-{{map_index}}-{{try_number}}'
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS=False
ENV AIRFLOW__CELERY__BROKER_URL=redis://172.22.0.1:6379/{1}
ENV AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://postgres:postgres@172.22.0.1:5433/{0}"
ENV AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth
ENV AIRFLOW__CORE__HIDE_SENSITIVE_VAR_CONN_FIELDS=False
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__SMTP__SMTP_HOST="172.22.0.1"
ENV AIRFLOW__SMTP__SMTP_PORT=1025
ENV AIRFLOW__SMTP__SMTP_STARTTLS=False
ENV AIRFLOW__SMTP__SMTP_SSL=False
ENV AIRFLOW__SMTP__SMTP_MAIL_FROM="airflow@{0}.com"
ENV AIRFLOW__SECRETS__BACKEND={3}
ENV AIRFLOW__SECRETS__BACKEND_KWARGS='{{"connections_path": "connections", "variables_path": "variables","config_path": "config", "mount_point": "airflow", "url": "http://172.22.0.1:8200", "token":"hvs.AlFE0WHKbruiBstNQURhQqz2"}}'
# ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN_SECRET=sql_alchemy_conn_value2
# ENV AIRFLOW__WEBSERVER__SECRET_KEY_SECRET=web_server_secret
ENV AIRFLOW__LINEAGE__BACKEND=openlineage.lineage_backend.OpenLineageBackend
ENV OPENLINEAGE_URL=http://172.22.0.1:5000
ENV OPENLINEAGE_NAMESPACE="{0}"
ENV ASTRONOMER_RUNTIME_EXECUTOR=false
ENV AIRFLOW__CORE__ENABLE_XCOM_PICKLING=True
ENV AIRFLOW__CORE__SENSITIVE_VAR_CONN_NAMES=credential
ENV AIRFLOW_CONN_MINIO_LOCAL='{{"conn_type": "aws", "extra": {{"aws_access_key_id": "minioadmin", "aws_secret_access_key": "minioadmin", "endpoint_url": "http://172.22.0.1:9000"}}}}'
ENV AIRFLOW_CONN_AWS_DEFAULT=${{AIRFLOW_CONN_MINIO_LOCAL}}
"""
DEV_DOCKERFILE = """FROM python:3.10-bullseye
RUN mkdir /usr/local/airflow
WORKDIR /usr/local/airflow
COPY . .
RUN apt-get update && cat packages.txt | xargs apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*;
RUN pip install wheel setuptools
RUN git clone https://github.com/apache/airflow.git
ENV AIRFLOW_HOME=/usr/local/airflow
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg 16" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get -y update && apt-get -y install postgresql-client patch yarn
RUN wget https://nodejs.org/dist/v18.12.1/node-v18.12.1-linux-arm64.tar.xz
RUN tar -C /usr/local --strip-components 1 -xvf node-v18.12.1-linux-arm64.tar.xz
RUN rm -rf node-v18.12.1-linux-arm64.tar.xz
RUN cd airflow && python setup.py compile_assets
RUN cd airflow && pip install .
RUN rm -rf airflow
RUN pip install -r requirements.txt
ENV AIRFLOW__CORE__FERNET_KEY=hspWEGdpVbFQmUKyvlwz3y-STqB54lGM1oui4mRQupw=
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://postgres:postgres@172.22.0.1:5433/{0}
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__WEBSERVER__RBAC=True
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
ENV AIRFLOW__LOGGING__REMOTE_LOGGING={2}
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=
ENV AIRFLOW__ELASTICSEARCH__FRONTEND="http://localhost:5601/app/kibana#/discover?_a=(columns:!(message),query:(language:kuery,query:'log_id: \"{{log_id}}\"'),sort:!(log.offset,asc))"
ENV AIRFLOW__ELASTICSEARCH__HOST=admin:admin@172.22.0.1:9200
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__USE_SSL=False
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__VERIFY_CERTS=False
ENV AIRFLOW__ELASTICSEARCH__JSON_FORMAT=False
ENV AIRFLOW__ELASTICSEARCH__HOST_FIELD=host.name
ENV AIRFLOW__ELASTICSEARCH__OFFSET_FIELD=offset
ENV AIRFLOW__ELASTICSEARCH__LOG_ID_TEMPLATE='{{dag_id}}-{{task_id}}-{{run_id}}-{{map_index}}-{{try_number}}'
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS=False
ENV AIRFLOW__CELERY__BROKER_URL=redis://172.22.0.1:6379/{1}
ENV AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://postgres:postgres@172.22.0.1:5433/{0}"
ENV AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth
ENV AIRFLOW__CORE__HIDE_SENSITIVE_VAR_CONN_FIELDS=False
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__SMTP__SMTP_HOST="172.22.0.1"
ENV AIRFLOW__SMTP__SMTP_PORT=1025
ENV AIRFLOW__SMTP__SMTP_STARTTLS=False
ENV AIRFLOW__SMTP__SMTP_SSL=False
ENV AIRFLOW__SMTP__SMTP_MAIL_FROM="airflow@{0}.com"
ENV AIRFLOW__SECRETS__BACKEND={3}
ENV AIRFLOW__SECRETS__BACKEND_KWARGS='{{"connections_path": "connections", "variables_path": "variables","config_path": "config", "mount_point": "airflow", "url": "http://172.22.0.1:8200", "token":"hvs.AlFE0WHKbruiBstNQURhQqz2"}}'
ENV AIRFLOW__LINEAGE__BACKEND=openlineage.lineage_backend.OpenLineageBackend
ENV OPENLINEAGE_URL=http://172.22.0.1:5000
ENV OPENLINEAGE_NAMESPACE="{0}"
ENV AIRFLOW__CORE__ENABLE_XCOM_PICKLING=True
ENV AIRFLOW__CORE__SENSITIVE_VAR_CONN_NAMES=credential
ENV AIRFLOW_CONN_MINIO_LOCAL='{{"conn_type": "aws", "extra": {{"aws_access_key_id": "minioadmin", "aws_secret_access_key": "minioadmin", "endpoint_url": "http://172.22.0.1:9000"}}}}'
ENV AIRFLOW_CONN_AWS_DEFAULT=${{AIRFLOW_CONN_MINIO_LOCAL}}
"""

OSS_DOCKERFILE = """FROM python:3.10-bullseye
RUN mkdir /usr/local/airflow
WORKDIR /usr/local/airflow
COPY . .
RUN apt-get update && cat packages.txt | xargs apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*;
RUN pip install wheel setuptools
ENV AIRFLOW_HOME=/usr/local/airflow
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt bullseye-pgdg 16" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get -y update && apt-get -y install postgresql-client patch
RUN pip install apache-airflow
RUN pip install -r requirements.txt
ENV AIRFLOW__CORE__FERNET_KEY=hspWEGdpVbFQmUKyvlwz3y-STqB54lGM1oui4mRQupw=
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://postgres:postgres@172.22.0.1:5433/{0}
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__WEBSERVER__RBAC=True
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
ENV AIRFLOW__LOGGING__REMOTE_LOGGING={2}
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=
ENV AIRFLOW__ELASTICSEARCH__FRONTEND="http://localhost:5601/app/kibana#/discover?_a=(columns:!(message),query:(language:kuery,query:'log_id: \"{{log_id}}\"'),sort:!(log.offset,asc))"
ENV AIRFLOW__ELASTICSEARCH__HOST=admin:admin@172.22.0.1:9200
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__USE_SSL=False
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__VERIFY_CERTS=False
ENV AIRFLOW__ELASTICSEARCH__JSON_FORMAT=False
ENV AIRFLOW__ELASTICSEARCH__HOST_FIELD=host.name
ENV AIRFLOW__ELASTICSEARCH__OFFSET_FIELD=offset
ENV AIRFLOW__ELASTICSEARCH__LOG_ID_TEMPLATE='{{dag_id}}-{{task_id}}-{{run_id}}-{{map_index}}-{{try_number}}'
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS=False
ENV AIRFLOW__CELERY__BROKER_URL=redis://172.22.0.1:6379/{1}
ENV AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://postgres:postgres@172.22.0.1:5433/{0}"
ENV AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth
ENV AIRFLOW__CORE__HIDE_SENSITIVE_VAR_CONN_FIELDS=False
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__SMTP__SMTP_HOST="172.22.0.1"
ENV AIRFLOW__SMTP__SMTP_PORT=1025
ENV AIRFLOW__SMTP__SMTP_STARTTLS=False
ENV AIRFLOW__SMTP__SMTP_SSL=False
ENV AIRFLOW__SMTP__SMTP_MAIL_FROM="airflow@{0}.com"
ENV AIRFLOW__SECRETS__BACKEND={3}
ENV AIRFLOW__SECRETS__BACKEND_KWARGS='{{"connections_path": "connections", "variables_path": "variables","config_path": "config", "mount_point": "airflow", "url": "http://172.22.0.1:8200", "token":"hvs.AlFE0WHKbruiBstNQURhQqz2"}}'
ENV AIRFLOW__LINEAGE__BACKEND=openlineage.lineage_backend.OpenLineageBackend
ENV OPENLINEAGE_URL=http://172.22.0.1:5000
ENV OPENLINEAGE_NAMESPACE="{0}"
ENV AIRFLOW__CORE__ENABLE_XCOM_PICKLING=True
ENV AIRFLOW__CORE__SENSITIVE_VAR_CONN_NAMES=credential
ENV AIRFLOW_CONN_MINIO_LOCAL='{{"conn_type": "aws", "extra": {{"aws_access_key_id": "minioadmin", "aws_secret_access_key": "minioadmin", "endpoint_url": "http://172.22.0.1:9000"}}}}'
ENV AIRFLOW_CONN_AWS_DEFAULT=${{AIRFLOW_CONN_MINIO_LOCAL}}
"""

LOGDOCKERFILE = """FROM opensearchproject/logstash-oss-with-opensearch-output-plugin:latest
RUN rm -f /usr/share/logstash/pipeline/logstash.conf
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf
USER root
RUN mkdir /usr/local/airflow
USER logstash
"""
# codec => "line" or "json"
LOGCONF = """# logstash.conf
input {
  file {
    path => [
      "/usr/local/airflow/logs/*/*/*/*.log"
    ]
    codec => multiline {
          pattern => "^\[[0-9\-T\:\.\+]+\]"
          negate => true
          what => "previous"
    }
  }
}
filter {
  if [log][file][path] {
    dissect {
      mapping => {
       "[log][file][path]" => "/usr/local/airflow/logs/dag_id=%{dag_id}/run_id=%{run_id}/task_id=%{task_id}/attempt=%{attempt}.log"
      }
    }
  }
  mutate {
    add_field => {
      "log_id" => "%{dag_id}-%{task_id}-%{run_id}--1-%{attempt}"
    }
  }
  mutate {
    gsub => [
      "message", "\[\\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]", "",
      "message", "\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]\]?", "",
      "message", "\\\\e",""
    ]
  }
  ruby {
      code => '
          time = Time.now
          event.set("offset", time.to_i * (10 ** 9) + time.nsec)
      '
  }
}
output {
  opensearch {
    hosts => [
      "172.22.0.1:9200"
    ]
    index => "filebeat-%{+YYYY.MM.dd}"
    user => "admin"
    password => "admin"
    ssl => false
    ssl_certificate_verification => false
    ecs_compatibility => disabled
  }
  stdout {
        codec => rubydebug
  }
}
"""

PACKAGES = """build-essential
iputils-ping
net-tools
iproute2
nano
vim
gnupg
wget
git
libpq-dev
"""

REQUIREMENTS = """apache-airflow-providers-elasticsearch
apache-airflow-providers-hashicorp
psycopg2
apache-airflow-providers-celery
redis
openlineage-airflow
astro-sdk-python[all]
"""

COMPOSE = """version: "3.8"
services:
  webserver:
    hostname: webserver
    image: {0}:latest
    ports:
      - "8080:8080"
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: airflow webserver
    networks:
      farm:
        ipv4_address: "172.22.0.104"
    extra_hosts:
      - "scheduler:172.22.0.105"
      - "triggerer:172.22.0.106"
      - "flower:172.22.0.108"
      - "worker-1:172.22.0.107"
      - "backup:172.22.0.109"
  scheduler:
    hostname: scheduler
    image: {0}:latest
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: airflow scheduler
    # command: airflow scheduler
    networks:
      farm:
        ipv4_address: "172.22.0.105"
    extra_hosts:
      - "webserver:172.22.0.104"
      - "triggerer:172.22.0.106"
      - "flower:172.22.0.108"
      - "worker-1:172.22.0.107"
      - "backup:172.22.0.109"
  triggerer:
    hostname: trigger
    image: {0}:latest
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: airflow triggerer
    # command: airflow triggerer
    networks:
      farm:
        ipv4_address: "172.22.0.106"
    extra_hosts:
      - "scheduler:172.22.0.105"
      - "webserver:172.22.0.104"
      - "flower:172.22.0.108"
      - "worker-1:172.22.0.107"
      - "backup:172.22.0.109"
  worker-1:
    hostname: worker-1
    image: {0}:latest
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: airflow celery worker -H "172.22.0.107"
    networks:
      farm:
        ipv4_address: "172.22.0.107"
    extra_hosts:
      - "scheduler:172.22.0.105"
      - "webserver:172.22.0.104"
      - "flower:172.22.0.108"
      - "triggerer:172.22.0.106"
      - "backup:172.22.0.109"
  flower:
    hostname: flower
    image: {0}:latest
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: airflow celery flower
    # command: airflow celery flower
    ports:
      - "5555:5555"
    depends_on:
      - worker-1
    networks:
      farm:
        ipv4_address: "172.22.0.108"
    extra_hosts:
      - "scheduler:172.22.0.105"
      - "webserver:172.22.0.104"
      - "worker-1:172.22.0.107"
      - "triggerer:172.22.0.106"
      - "backup:172.22.0.109"
  backup:
    hostname: backup
    image: {0}:latest
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    command: sleep infinity
    networks:
      farm:
        ipv4_address: "172.22.0.109"
    extra_hosts:
      - "scheduler:172.22.0.105"
      - "webserver:172.22.0.104"
      - "worker-1:172.22.0.107"
      - "triggerer:172.22.0.106"
      - "flower:172.22.0.108"
  logstash:
    hostname: logstash
    build:
      context: .
      dockerfile: log.Dockerfile
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    networks:
      farm:
        ipv4_address: "172.22.0.110"
  {2}
volumes:
  dags:
    driver: local
    driver_opts:
      o: bind
      type: none
      device: {1}/dags
  logs:
  plugins:
    driver: local
    driver_opts:
      o: bind
      type: none
      device: {1}/plugins
  include:
    driver: local
    driver_opts:
      o: bind
      type: none
      device: {1}/include
  sincedb:
    driver: local
    driver_opts:
      o: bind
      type: none

networks:
  farm:
    external: true
    ipam:
      config:
        - subnet: "172.22.0.1/16"
          gateway: "172.22.0.1"
          aux_addresses:
            webserver: "172.22.0.104"
            scheduler: "172.22.0.105"
            trigger: "172.22.0.106"
            flower: "172.22.0.107"
            worker-1: "172.22.0.108"
            backup: "172.22.0.109"
      
      """
COMPOSE_CODE = """code:
    hostname: code
    build:
      context: .
      dockerfile: code.Dockerfile
    volumes:
      - dags:/usr/local/airflow/dags
      - logs:/usr/local/airflow/logs
      - plugins:/usr/local/airflow/plugins
      - include:/usr/local/airflow/include
    ports:
      - "7000:7000"
    networks:
      farm:
        ipv4_address: "172.22.0.111"
        """
START = """echo "Deploying..."
docker-compose ls | grep farm > start.log 2>&1  
if [ $? -ne 0 ]
then 
    echo "Farm doesn't exist. Creating..."
    docker network create -d bridge --gateway 172.22.0.1 --subnet 172.22.0.1/16 farm ;
    docker-compose  -f ../farm/docker-compose.yml up -d
fi
echo "Cleaning older deployment..."
docker-compose down >> start.log 2>&1  
docker volume prune -f >> start.log 2>&1  ;
echo "Building image..."
docker build --no-cache -t {0}:latest .  >> start.log 2>&1  
if [ $? -ne 0 ]
then 
    echo "Build failed. Exiting..."
    exit 1
fi
echo "Preping db..."
docker run -it --net farm -e PGPASSWORD=postgres {0}:latest psql -h 172.22.0.1 -p 5433 -U postgres -c 'CREATE DATABASE "{0}";' >> start.log 2>&1  
if [ $? -eq 0 ]
then 
    docker run -it --net farm  {0}:latest airflow db init >> start.log 2>&1
    docker run -it --net farm {0}:latest airflow users create --username admin --firstname FIRST_NAME  --lastname LAST_NAME --role Admin --email admin@example.org --password admin >> start.log 2>&1  
else
    docker run -it --net farm  {0}:latest airflow db upgrade >> start.log 2>&1  
fi
alias decolorize='sed -r "s/\\x1B\\[([0-9]{{1,3}}(;[0-9]{{1,2}})?)?[mGK]//g"'
cp start.log start_clr.log
cat start_clr.log | decolorize > start.log 
rm start_clr.log
docker-compose up -d --build >> start.log 2>&1  
echo "Deployed:"
echo "Airflow: http://localhost:8080"
echo "Airflow Swagger: http://localhost:8080/api/v1/ui/"
echo "Flower: http://localhost:5555"
echo "IDE: http://localhost:7000"
echo "Vault: http://localhost:8200"
echo "Opensearch: http://localhost:5601/app/home#/"
echo "Marquez: http://localhost:3000/"
"""

STOP = """docker-compose down"""

CLEAN = """sed -r '/^\s*$/d' $1 > tmpfile && mv tmpfile $1"""

VAULTDOCKER = """FROM vault:latest
COPY vault.json /vault/config/vault.json
CMD ["vault", "server", "-config=/vault/config/vault.json"]
"""
VAULTJSON = """{         
  "ui" : "true",
  "disable_mlock" : "true",                        
  "listener":  {                     
    "tcp":  {                        
      "address":  "0.0.0.0:8200",  
      "tls_disable":  "true"         
    }                                
  },                                 
  "backend": {                       
    "file": {                        
      "path": "/vault/file"          
    }                                
  },                                 
  "default_lease_ttl": "168h",       
  "max_lease_ttl": "0h",
  "api_addr": "http://0.0.0.0:8200"

}
"""

FARMSTART = """docker network create -d bridge --gateway 172.22.0.1 --subnet 172.22.0.1/16 farm ;
docker-compose up -d
"""

FARMCOMPOSE = """services:
  database:
    image: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    ports:
      - "5433:5432"
    networks:
      farm:
        ipv4_address: 172.22.0.2
    volumes:
      - pg_data:/var/lib/postgresql/data:rw
  redis:
    build:
      context: .
      dockerfile: redis.Dockerfile
    environment:
      REDIS_PORT_6379_TCP_ADDR: redis
      REDIS_PORT_6379_TCP_PORT: 6379
    ports:
      - "6379:6379"
    networks:
      farm:
        ipv4_address: 172.22.0.3
    entrypoint: redis-server
  vault:
    build:
      context: .
      dockerfile: vault.Dockerfile
    environment:
      VAULT_ADDR: http://127.0.0.1:8200
      # This token needs to be generated when spinning up first time if need to execute vault cli
      VAULT_TOKEN: hvs.3A6OCnFe7wO474PZsOZZyZZi
      VAULT_DEV_ROOT_TOKEN_ID: myroot
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
      VAULT_LOCAL_CONFIG={"backend": '{"file": {"path": "/vault/file"}}'
    cap_add:
      - IPC_LOCK
    volumes:
      - vault_db:/vault/file
    ports:
      - "8200:8200"
    networks:
      farm:
        ipv4_address: 172.22.0.4
  smtp:
    build:
      context: .
      dockerfile: smtp.Dockerfile
    ports:
      - "1025:1025"
    networks:
      farm:
        ipv4_address: 172.22.0.5
    command: sendria --db mails.sqlite --smtp-ip=0.0.0.0 --http-ip=0.0.0.0
  opensearch-node1:
    image: opensearchproject/opensearch:latest
    hostname: opensearch-node1
    environment:
      - cluster.name=opensearch-cluster # Name the cluster
      - node.name=opensearch-node1 # Name the node that will run in this container
      - discovery.seed_hosts=opensearch-node1,opensearch-node2 # Nodes to look for when discovering the cluster
      - cluster.initial_cluster_manager_nodes=opensearch-node1,opensearch-node2 # Nodes eligibile to serve as cluster manager
      - bootstrap.memory_lock=true # Disable JVM heap memory swapping
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" # Set min and max JVM heap sizes to at least 50% of system RAM
      - "DISABLE_INSTALL_DEMO_CONFIG=true" # Prevents execution of bundled demo script which installs demo certificates and security configurations to OpenSearch
      - "DISABLE_SECURITY_PLUGIN=true" # Disables security plugin
    ulimits:
      memlock:
        soft: -1 # Set memlock to unlimited (no soft or hard limit)
        hard: -1
      nofile:
        soft: 65536 # Maximum number of open files for the opensearch user - set to at least 65536
        hard: 65536
    volumes:
      - opensearch-data1:/usr/share/opensearch/data # Creates volume called opensearch-data1 and mounts it to the container
    ports:
      - 9200:9200 # REST API
      - 9600:9600 # Performance Analyzer
    networks:
      farm:
        ipv4_address: 172.22.0.6
  opensearch-node2:
    image: opensearchproject/opensearch:latest
    hostname: opensearch-node2
    environment:
      - cluster.name=opensearch-cluster # Name the cluster
      - node.name=opensearch-node2 # Name the node that will run in this container
      - discovery.seed_hosts=opensearch-node1,opensearch-node2 # Nodes to look for when discovering the cluster
      - cluster.initial_cluster_manager_nodes=opensearch-node1,opensearch-node2 # Nodes eligibile to serve as cluster manager
      - bootstrap.memory_lock=true # Disable JVM heap memory swapping
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" # Set min and max JVM heap sizes to at least 50% of system RAM
      - "DISABLE_INSTALL_DEMO_CONFIG=true" # Prevents execution of bundled demo script which installs demo certificates and security configurations to OpenSearch
      - "DISABLE_SECURITY_PLUGIN=true" # Disables security plugin
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - opensearch-data2:/usr/share/opensearch/data
    networks:
      farm:
        ipv4_address: 172.22.0.7
  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:latest
    hostname: opensearch-dashboards
    ports:
      - 5601:5601
    expose:
      - "5601"
    environment:
      - 'OPENSEARCH_HOSTS=["http://opensearch-node1:9200","http://opensearch-node2:9200"]'
      - "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" # disables security dashboards plugin in OpenSearch Dashboards
    networks:
      farm:
        ipv4_address: 172.22.0.8
  lineageapi:
    image: "marquezproject/marquez:latest"
    hostname: marquez-api
    environment:
      - MARQUEZ_PORT=5000
      - MARQUEZ_ADMIN_PORT=5001
      - POSTGRES_HOST=172.22.0.1
      - POSTGRES_PORT=5434
      - POSTGRES_DB=marquez
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez
    ports:
      - "5000:5000"
      - "5001:5001"
    volumes:
      - utils:/opt/marquez
      - ./marquez.dev.yml:/usr/src/app/marquez.dev.yml
    depends_on:
      - lineagedb
    entrypoint: ["./entrypoint.sh"]
    networks:
      farm:
        ipv4_address: 172.22.0.9
  lineageweb:
    image: "marquezproject/marquez-web:latest"
    hostname: marquez-web
    environment:
      - MARQUEZ_HOST=172.22.0.1
      - MARQUEZ_PORT=5000
    ports:
      - "3000:3000"
    stdin_open: true
    tty: true
    depends_on:
      - lineageapi
    networks:
      farm:
        ipv4_address: 172.22.0.10
  lineagedb:
    image: postgres:12.1
    hostname: marquez-db
    ports:
      - "5434:5432"
    environment:
      - POSTGRES_DB=marquez
      - POSTGRES_USER=marquez
      - POSTGRES_PASSWORD=marquez
    volumes:
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
      - marq_pg:/var/lib/postgresql/data:rw
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
    networks:
      farm:
        ipv4_address: 172.22.0.11
  minio:
    image: quay.io/minio/minio
    networks:
      farm:
        ipv4_address: 172.22.0.12
    command: server /data --console-address ":9001"
    ports:
      - 9000:9000
      - 9001:9001
    volumes:
       - ./miniodata:/data
    
version: '3.8'
volumes:
  pg_data:
  opensearch-data1:
  opensearch-data2:
  vault_db:
  utils:
  marq_pg:

networks:
  farm:
    external: true
"""
MARQUEZPOSTGRESCONF = """shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 10000
track_activity_query_size = 2048

listen_addresses = '*'
"""

FARMSMTPDOCKER = """FROM python:3.9
RUN pip install sendria
EXPOSE 1025
"""

CODEDOCKERFILE = """FROM codercom/code-server:latest
USER root
RUN mkdir /usr/local/airflow && chmod -R 766 /usr/local/airflow
RUN mkdir -p .config/code-server
ARG DEFAULT_WORKSPACE=/usr/local/airflow
ENV PASSWORD=admin
ENTRYPOINT ["/usr/bin/code-server","--bind-addr","0.0.0.0:7000","--disable-telemetry","--auth","password","/usr/local/airflow"]"""

REDISDOCKERFILE = """FROM redis:latest
RUN mkdir /usr/local/etc/redis
RUN echo "databases 1000" >> /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]"""

MARQUEZCONF = """server:
  applicationConnectors:
  - type: http
    port: ${MARQUEZ_PORT:-5000}
    httpCompliance: RFC7230_LEGACY
  adminConnectors:
  - type: http
    port: ${MARQUEZ_ADMIN_PORT:-5001}

db:
  driverClass: org.postgresql.Driver
  url: jdbc:postgresql://${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
  user: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}

migrateOnStartup: true

graphql:
  enabled: true

logging:
  level: DEBUG
  appenders:
    - type: console

tags:
  - name: PII
    description: Personally identifiable information
  - name: SENSITIVE
    description: Contains sensitive information
"""

ANGRY = "ヽ(`⌒´メ)ノ"
OOPS = "¯\_(ツ)_/¯"
CONFUSED = "(￢_￢;)"
YAY = "(￣▽￣)ノ"
WORKING = "__φ(。。)"
UNSATISFIED = "(￢_￢)"
SAYONARA = "凸(￣ヘ￣)"