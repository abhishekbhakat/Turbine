import click
import json
import os
import shutil
import stat
from turbine.farm_utils.composer import get_or_create_farm
from turbine.farm_utils import delete
from turbine.dockerfile_templates import (
    AIRFLOW_DOCKERFILE,
    CODE_SERVER_DOCKERFILE,
    LOGSTASH_DOCKERFILE,
)

# Kaomoji for added character
WORKING = "ᕦ(ò_óˇ)ᕤ"
YAY = "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
ANGRY = "(╯°□°）╯︵ ┻━┻"
CONFUSED = "(-_-;)・・・"
UNSATISFIED = "(－‸ლ)"
COOL = "(⌐■_■)"

@click.group()
def cli():
    """Turbine CLI for managing Airflow deployments"""
    pass

@cli.command()
def init_farm():
    """Initialize the farm"""
    get_or_create_farm()
    click.echo(f"Farm initialized {COOL}")

def get_next_redis_db():
    cache_file = ".cache"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)
        used_dbs = [project.get("redisdb", 0) for project in cache.values()]
        return max(used_dbs) + 1 if used_dbs else 0
    return 0

@cli.command()
def create_project():
    """Create a new Airflow project"""
    # Ensure farm is initialized before creating a project
    if not os.path.exists('farm'):
        click.echo(f"Farm not initialized. Initializing farm... {WORKING}")
        get_or_create_farm()
        click.echo(f"Farm initialized {COOL}")

    name = click.prompt("Project name", type=str)
    
    click.echo("Airflow type:")
    click.echo("1. Astro [default]")
    click.echo("2. OSS")
    click.echo("3. OSS Main branch")
    airflow_type_choice = click.prompt("Choose Airflow type", type=click.Choice(['1', '2', '3', '']), default='1')
    
    if airflow_type_choice == '1' or airflow_type_choice == '':
        airflow_type = 'astro'
    elif airflow_type_choice == '2':
        airflow_type = 'oss'
    else:
        airflow_type = 'oss_dev'

    remote_logging = click.confirm("Enable remote logging?", default=True)
    
    if remote_logging:
        click.echo("Remote logging type:")
        click.echo("1. S3 [default]")
        click.echo("2. Elasticsearch")
        remote_logging_type = click.prompt("Choose remote logging type", type=click.Choice(['1', '2', '']), default='1')
        if remote_logging_type == '1' or remote_logging_type == '':
            docker_remote_con_id = "aws_default"
            docker_remote_base_folder = f"s3://{name.lower()}"
        else:
            docker_remote_con_id = ""
            docker_remote_base_folder = ""
    else:
        docker_remote_con_id = ""
        docker_remote_base_folder = ""

    vault = click.confirm("Enable Vault?", default=False)
    code_server = click.confirm("Enable Code Server?", default=False)

    tgt_folder = f"{name.lower()}-{airflow_type}-airflow"
    
    if os.path.exists(tgt_folder):
        click.echo(f"Project {tgt_folder} already exists! {CONFUSED}")
        return

    click.echo(f"Creating project {tgt_folder}... {WORKING}")
    
    os.makedirs(tgt_folder)
    os.makedirs(os.path.join(tgt_folder, "dags"))
    os.makedirs(os.path.join(tgt_folder, "logs"))
    os.makedirs(os.path.join(tgt_folder, "plugins"))

    # Get the next available Redis database number
    redisdb = get_next_redis_db()

    # Write Dockerfile
    dockerfile_content = AIRFLOW_DOCKERFILE.format(
        redisdb=redisdb,
        remote_login=str(remote_logging).lower(),
        vault_backend='"airflow.providers.hashicorp.secrets.vault.VaultBackend"' if vault else '""',
        docker_remote_base_folder=docker_remote_base_folder,
        docker_remote_con_id=docker_remote_con_id
    )
    with open(os.path.join(tgt_folder, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

    # Write project-specific docker-compose.yaml
    docker_compose_content = f"""
version: '3'
x-airflow-common:
  &airflow-common
  build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/{redisdb}
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKEND: 'airflow.api.auth.backend.basic_auth'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${{AIRFLOW_UID:-50000}}:0"
  depends_on:
    &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

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
      interval: 5s
      retries: 5
    restart: always

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - 8080:8080
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "${{HOSTNAME}}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@${{HOSTNAME}}"'
      interval: 10s
      timeout: 10s
      retries: 5
    environment:
      <<: *airflow-common-env
      # Required to handle warm shutdown of the celery workers properly
      # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "${{HOSTNAME}}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        function ver() {{
          printf "%04d%04d%04d%04d" ${{1//./ /0}} ${{2//./ /0}} ${{3//./ /0}} ${{4//./ /0}}
        }}
        airflow_version=${{(gosu airflow airflow version)}}
        airflow_version_comparable=${{(ver $airflow_version)}}
        min_airflow_version=2.2.0
        min_airflow_version_comparable=${{(ver $min_airflow_version)}}
        if (( airflow_version_comparable < min_airflow_version_comparable )); then
          echo
          echo -e "\033[1;31mERROR!!!: Too old Airflow version ${{airflow_version}}!\e[0m"
          echo "The minimum Airflow version supported: ${{min_airflow_version}}. Only use this or higher!"
          echo
          exit 1
        fi
        if [[ -z "${{AIRFLOW_UID}}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#setting-the-right-airflow-user"
          echo
        fi
        one_meg=1048576
        mem_available=${{((${{(getconf _PHYS_PAGES)}} * ${{(getconf PAGE_SIZE)}}) / one_meg)}}
        cpus_available=${{(grep -cE 'cpu[0-9]+' /proc/stat)}}
        disk_available=${{(df / | tail -1 | awk '{{print $4}}')}}
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have ${{mem_available}}MB"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have ${{cpus_available}}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have ${{disk_available / one_meg}}GB"
          echo
          warning_resources="true"
        fi
        if [[ ${{warning_resources}} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#before-you-begin"
          echo
        fi
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${{AIRFLOW_UID:-50000}}:0" /sources/{{logs,dags,plugins}}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${{_AIRFLOW_WWW_USER_USERNAME:-airflow}}
      _AIRFLOW_WWW_USER_PASSWORD: ${{_AIRFLOW_WWW_USER_PASSWORD:-airflow}}
    user: "0:0"
    volumes:
      - .:/sources

volumes:
  postgres-db-volume:
"""
    with open(os.path.join(tgt_folder, "docker-compose.yaml"), "w") as f:
        f.write(docker_compose_content)

    # Write start.sh
    start_script_content = f"""#!/bin/bash
docker-compose up -d
echo "Airflow project {tgt_folder} is running!"
echo "Webserver will be available at http://localhost:8080"
"""
    start_script_path = os.path.join(tgt_folder, "start.sh")
    with open(start_script_path, "w") as f:
        f.write(start_script_content)
    os.chmod(start_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Write stop.sh
    stop_script_content = f"""#!/bin/bash
docker-compose down
echo "Airflow project {tgt_folder} has been stopped."
"""
    stop_script_path = os.path.join(tgt_folder, "stop.sh")
    with open(stop_script_path, "w") as f:
        f.write(stop_script_content)
    os.chmod(stop_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    if code_server:
        code_dockerfile_content = CODE_SERVER_DOCKERFILE.format(code_p=8080)  # You may want to dynamically assign this port
        with open(os.path.join(tgt_folder, "code.Dockerfile"), "w") as f:
            f.write(code_dockerfile_content)

    # Update cache
    cache_file = ".cache"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)
    else:
        cache = {}

    cache[tgt_folder] = {
        "type": airflow_type,
        "remote_logging": remote_logging,
        "vault": vault,
        "code_server": code_server,
        "redisdb": redisdb
    }

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=4)

    click.echo(f"Project {tgt_folder} created successfully! {YAY}")

@cli.command()
@click.argument('project_name')
def start_project(project_name):
    """Start an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return
    
    click.echo(f"Starting project {project_name}... {WORKING}")
    os.system(f"cd {project_name} && ./start.sh")
    click.echo(f"Project {project_name} started! {COOL}")

@cli.command()
@click.argument('project_name')
def stop_project(project_name):
    """Stop an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return
    
    click.echo(f"Stopping project {project_name}... {WORKING}")
    os.system(f"cd {project_name} && ./stop.sh")
    click.echo(f"Project {project_name} stopped! {COOL}")

@cli.command()
@click.argument('project_name')
def delete_project(project_name):
    """Delete an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return
    
    click.echo(f"Deleting project {project_name}... {WORKING}")
    delete.delete_proj(project_name)
    click.echo(f"Project {project_name} deleted! {COOL}")

@cli.command()
def delete_farm():
    """Delete the entire farm and all projects"""
    click.echo(f"Deleting farm and all projects... {WORKING}")
    delete.delete_all()
    click.echo(f"Farm and all projects deleted! {COOL}")

@cli.command()
def list_projects():
    """List all Airflow projects"""
    cache_file = ".cache"
    if not os.path.exists(cache_file):
        click.echo(f"No projects found! {CONFUSED}")
        return
    
    with open(cache_file) as f:
        airflows = json.load(f)
    
    if not airflows:
        click.echo(f"No projects found! {CONFUSED}")
        return
    
    click.echo(f"Airflow projects: {COOL}")
    for project in airflows.keys():
        click.echo(f"- {project}")

if __name__ == '__main__':
    cli()