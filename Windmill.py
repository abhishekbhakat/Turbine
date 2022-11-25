import os, sys, stat, socket, subprocess, base64

DOCKERFILE = """FROM python:3.9-bullseye
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
RUN apt-get -y update && apt-get -y install postgresql-client patch
RUN pip install apache-airflow
RUN pip install -r requirements.txt
ENV AIRFLOW__CORE__FERNET_KEY={1}
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://postgres:postgres@172.22.0.1:5432/{0}
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__WEBSERVER__RBAC=True
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=DEBUG
ENV AIRFLOW__LOGGING__REMOTE_LOGGING=True
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=
ENV AIRFLOW__ELASTICSEARCH__FRONTEND="http://localhost:5601/app/kibana#/discover?_a=(columns:!(message),query:(language:kuery,query:'log_id: \"{{log_id}}\"'),sort:!(log.offset,asc))"
ENV AIRFLOW__ELASTICSEARCH__HOST=admin:admin@172.22.0.1:9200
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__USE_SSL=False
ENV AIRFLOW__ELASTICSEARCH_CONFIGS__VERIFY_CERTS=False
ENV AIRFLOW__ELASTICSEARCH__JSON_FORMAT=True
ENV AIRFLOW__ELASTICSEARCH__HOST_FIELD=host.name
ENV AIRFLOW__ELASTICSEARCH__OFFSET_FIELD=offset
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__DATABASE__LOAD_DEFAULT_CONNECTIONS=False
ENV AIRFLOW__CELERY__BROKER_URL=redis://172.22.0.1:6379/1
ENV AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://postgres:postgres@172.22.0.1:5432/{0}"
ENV AIRFLOW__API__AUTH_BACKENDS=airflow.api.auth.backend.basic_auth
ENV AIRFLOW__CORE__HIDE_SENSITIVE_VAR_CONN_FIELDS=False
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
ENV AIRFLOW__SMTP__SMTP_HOST="172.22.0.1"
ENV AIRFLOW__SMTP__SMTP_PORT=1025
ENV AIRFLOW__SMTP__SMTP_STARTTLS=False
ENV AIRFLOW__SMTP__SMTP_SSL=False
ENV AIRFLOW__SMTP__SMTP_MAIL_FROM="airflow@{0}.com"
ENV AIRFLOW__SECRETS__BACKEND=airflow.providers.hashicorp.secrets.vault.VaultBackend
ENV AIRFLOW__SECRETS__BACKEND_KWARGS='{{"connections_path": "connections", "variables_path": "variables","config_path": "config", "mount_point": "airflow", "url": "http://172.22.0.1:8200", "token":"hvs.AlFE0WHKbruiBstNQURhQqz2"}}'
# ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN_SECRET=sql_alchemy_conn_value2
# ENV AIRFLOW__WEBSERVER__SECRET_KEY_SECRET=web_server_secret
"""

LOGDOCKERFILE = """FROM opensearchproject/logstash-oss-with-opensearch-output-plugin:latest
RUN rm -f /usr/share/logstash/pipeline/logstash.conf
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf
USER root
RUN mkdir /usr/local/airflow
USER logstash
"""
#codec => "line" or "json"
LOGCONF = """# logstash.conf
input {
  file {
    path => ["/usr/local/airflow/logs/*/*/*/*.log"]
    codec => "json"
  }
}
output {
  opensearch {
    hosts => ["172.22.0.1:9200"]
    index => "{0}-%{+YYYY.MM.dd}"
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

PACKAGES = """iputils-ping
net-tools
iproute2
nano
vim
gnupg
wget
git
"""

REQUIREMENTS = """apache-airflow-providers-elasticsearch
apache-airflow-providers-hashicorp
psycopg2
apache-airflow-providers-celery
redis
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
    restart: always
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

# networks:
#   compose:
#     driver: farm
#     ipam:
#       driver: farm
#       config:
#         - subnet: 172.22.0.0/16
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
START = """echo "Deploying..."
docker-compose ls | grep farm > start.log 2>&1  
if [ $? -ne 0 ]
then 
    echo "Farm doesn't exist. Creating..."
    cd ../farm && ./start.sh
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
docker run -it --net farm -e PGPASSWORD=postgres {0}:latest psql -h 172.22.0.1 -U postgres -c 'CREATE DATABASE "{0}";' >> start.log 2>&1  
if [ $? -eq 0 ]
then 
    docker run -it --net farm  {0}:latest airflow db init && \
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
echo "Vault: http://localhost:8200"
echo "Opensearch: http://localhost:5601/app/home#/"
"""

STOP="""docker-compose down"""

CLEAN = """sed -r '/^\s*$/d' $1 > tmpfile && mv tmpfile $1"""

VAULTDOCKER="""FROM vault:latest
COPY vault.json /vault/config/vault.json
CMD ["vault", "server", "-config=/vault/config/vault.json"]
"""
VAULTJSON="""{         
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

FARMSTART="""docker network create -d bridge --gateway 172.22.0.1 --subnet 172.22.0.1/16 farm
docker-compose up -d
"""

FARMCOMPOSE="""services:
  database:
    image: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    networks:
      farm:
        ipv4_address: 172.22.0.2
    volumes:
      - pg_data:/var/lib/postgresql/data:rw
  redis:
    image: redis:6-bullseye
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
      VAULT_TOKEN: hvs.AlFE0WHKbruiBstNQURhQqz2
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
    container_name: opensearch-node1
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
    container_name: opensearch-node2
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
    container_name: opensearch-dashboards
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
version: '3.8'
volumes:
  pg_data:
  opensearch-data1:
  opensearch-data2:
  vault_db:

networks:
  farm:
    external: true
"""

FARMSMTPDOCKER="""FROM python:3.9
RUN pip install sendria
EXPOSE 1025
"""

def get_or_create_farm():
  farm = 'farm'
  if not os.path.exists(farm):
    print("Creating new farm...")
    os.makedirs(farm)
    with open(os.path.join(farm,'vault.Dockerfile'),'w') as f:
        f.write(VAULTDOCKER.format(farm))
    with open(os.path.join(farm,'vault.json'),'w') as f:
        f.write(VAULTJSON)
    with open(os.path.join(farm,'start.sh'),'w') as f:
        f.write(FARMSTART)
    with open(os.path.join(farm,'smtp.Dockerfile'),'w') as f:
        f.write(FARMSMTPDOCKER)
    with open(os.path.join(farm,'docker-compose.yml'),'w') as f:
        f.write(FARMCOMPOSE)
    os.chmod(os.path.join(farm,'start.sh'), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    print("New farm created using network as 172.22.0.1/16!")
  else:
    print("Existing farm found!")

def porter(init):
  result = 1
  for i in range(init,65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1',i))
    sock.close()
    if result != 0:
      break
  return i

def get_network():
  for i in range(255):
    cmd = "grep -rl '172.22.{}' *"
    res = subprocess.Popen([cmd.format(i)],shell=True, stdout=subprocess.DEVNULL)
    res.communicate()
    if res.returncode == 1:
        break
  return '172.22.{}'.format(i)

def create_folder_and_copy_utils(folder_name): 
    web_p = porter(8080)
    flower_p = porter(5555)     
    network = get_network()
    print('Using port {} for webserver and {} for flower.'.format(str(web_p),str(flower_p)))
    print('Using network: '+network+'.1')
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        os.makedirs(os.path.join(folder_name,'dags'))
        os.makedirs(os.path.join(folder_name,'logs'))
        os.makedirs(os.path.join(folder_name,'plugins'))
        os.makedirs(os.path.join(folder_name,'include'))
    else:
        print("The folder already exists!")
        sys.exit()
    with open(os.path.join(folder_name,'Dockerfile'),'w') as f:
        key = "{} is a local dev project, Do not use in production.".format(folder_name)
        fernet = base64.b64encode(key.encode('ascii')).decode("ascii")
        f.write(DOCKERFILE.format(folder_name,fernet))
    with open(os.path.join(folder_name,'packages.txt'),'w') as f:
        f.write(PACKAGES)
    with open(os.path.join(folder_name,'docker-compose.yaml'),'w') as f:
        draft = COMPOSE.format(folder_name,"${PWD}").replace('8080:8080',str(web_p)+':8080').replace('5555:5555',str(flower_p)+':5555')
        draft = draft.replace('172.22.0',network)
        f.write(draft)
    with open(os.path.join(folder_name,'start.sh'),'w') as f:
        f.write(START.format(folder_name).replace('8080',str(web_p)).replace('5555',str(flower_p)))
    with open(os.path.join(folder_name,'stop.sh'),'w') as f:
        f.write(STOP)
    with open(os.path.join(folder_name,'clean.sh'),'w') as f:
        f.write(CLEAN)
    with open(os.path.join(folder_name,'log.Dockerfile'),'w') as f:
        f.write(LOGDOCKERFILE)
    with open(os.path.join(folder_name,'logstash.conf'),'w') as f:
        f.write(LOGCONF.replace('filebeat',folder_name))
    with open(os.path.join(folder_name,'requirements.txt'),'w') as f:
        f.write(REQUIREMENTS)
    os.chmod(os.path.join(folder_name,'start.sh'), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    os.chmod(os.path.join(folder_name,'stop.sh'), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    os.chmod(os.path.join(folder_name,'clean.sh'), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)



get_or_create_farm()
tgt_folder = input("Folder name: ")
create_folder_and_copy_utils(tgt_folder)

# Make sure network 172.22.0.1 is not being used. Or else change all occurence of 172.22 with a suitable network address.
# Create project only when running all other Airflows else it could cause port reusage