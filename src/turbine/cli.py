import json
import os
import stat

import click

from turbine.cache import (
    add_project_to_cache,
    generate_db_name,
    get_next_flower_port,
    get_next_network,
    get_next_redis_db,
    get_next_webserver_port,
    load_cache,
)
from turbine.dockerfile_templates import (
    AIRFLOW_DOCKERFILE,
    CODE_SERVER_DOCKERFILE,
)
from turbine.farm_utils import delete
from turbine.farm_utils.composer import get_or_create_farm
from turbine.templates import (
    PROJECT_DOCKER_COMPOSE_TEMPLATE,
    PROJECT_START_SCRIPT_TEMPLATE,
    PROJECT_STOP_SCRIPT_TEMPLATE,
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


@cli.command()
def create_project():
    """Create a new Airflow project"""
    # Ensure farm is initialized before creating a project
    if not os.path.exists("farm"):
        click.echo(f"Farm not initialized. Initializing farm... {WORKING}")
        get_or_create_farm()
        click.echo(f"Farm initialized {COOL}")

    cache = load_cache()

    name = click.prompt("Project name", type=str)

    click.echo("Airflow type:")
    click.echo("1. Astro [default]")
    click.echo("2. OSS")
    click.echo("3. OSS Main branch")
    airflow_type_choice = click.prompt("Choose Airflow type", type=click.Choice(["1", "2", "3", ""]), default="1")

    if airflow_type_choice == "1" or airflow_type_choice == "":
        airflow_type = "astro"
    elif airflow_type_choice == "2":
        airflow_type = "oss"
    else:
        airflow_type = "oss_dev"

    remote_logging = click.confirm("Enable remote logging?", default=True)

    if remote_logging:
        click.echo("Remote logging type:")
        click.echo("1. S3 [default]")
        click.echo("2. Elasticsearch")
        remote_logging_type = click.prompt("Choose remote logging type", type=click.Choice(["1", "2", ""]), default="1")
        if remote_logging_type == "1" or remote_logging_type == "":
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

    # Get the next available ports and resources
    webserver_port = get_next_webserver_port(cache)
    flower_port = get_next_flower_port(cache)
    redisdb = get_next_redis_db(cache)
    network = get_next_network(cache)
    db_name = generate_db_name(tgt_folder)

    # Write Dockerfile
    dockerfile_content = AIRFLOW_DOCKERFILE.format(
        project_name=tgt_folder,
        redisdb=redisdb,
        remote_login=str(remote_logging).lower(),
        vault_backend='"airflow.providers.hashicorp.secrets.vault.VaultBackend"' if vault else '""',
        arch="amd64",  # You might want to make this dynamic based on the system architecture
        docker_remote_con_id=docker_remote_con_id,
        docker_remote_base_folder=docker_remote_base_folder,
    )
    with open(os.path.join(tgt_folder, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

    # Write project-specific docker-compose.yaml
    docker_compose_content = PROJECT_DOCKER_COMPOSE_TEMPLATE.format(tgt_folder=tgt_folder, db_name=db_name, redisdb=redisdb, webserver_port=webserver_port, flower_port=flower_port)
    with open(os.path.join(tgt_folder, "docker-compose.yaml"), "w") as f:
        f.write(docker_compose_content)

    # Write start.sh
    start_script_content = PROJECT_START_SCRIPT_TEMPLATE.format(db_name=db_name, tgt_folder=tgt_folder, webserver_port=webserver_port, flower_port=flower_port)
    start_script_path = os.path.join(tgt_folder, "start.sh")
    with open(start_script_path, "w") as f:
        f.write(start_script_content)
    os.chmod(start_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Write stop.sh
    stop_script_content = PROJECT_STOP_SCRIPT_TEMPLATE.format(tgt_folder=tgt_folder)
    stop_script_path = os.path.join(tgt_folder, "stop.sh")
    with open(stop_script_path, "w") as f:
        f.write(stop_script_content)
    os.chmod(stop_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    if code_server:
        code_dockerfile_content = CODE_SERVER_DOCKERFILE.format(code_p=8080)  # You may want to dynamically assign this port
        with open(os.path.join(tgt_folder, "code.Dockerfile"), "w") as f:
            f.write(code_dockerfile_content)

    # Update cache
    project_data = {"type": airflow_type, "remote_logging": remote_logging, "vault": vault, "code_server": code_server, "redisdb": redisdb, "webserver": webserver_port, "flower": flower_port, "network": network, "db_name": db_name}
    add_project_to_cache(cache, tgt_folder, project_data)

    click.echo(f"Project {tgt_folder} created successfully! {YAY}")
    click.echo(f"Webserver port: {webserver_port}")
    click.echo(f"Flower port: {flower_port}")
    click.echo(f"Redis DB: {redisdb}")
    click.echo(f"Network: {network}")
    click.echo(f"Database name: {db_name}")


@cli.command()
@click.argument("project_name")
def start_project(project_name):
    """Start an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return

    click.echo(f"Starting project {project_name}... {WORKING}")
    os.system(f"cd {project_name} && ./start.sh")
    click.echo(f"Project {project_name} started! {COOL}")


@cli.command()
@click.argument("project_name")
def stop_project(project_name):
    """Stop an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return

    click.echo(f"Stopping project {project_name}... {WORKING}")
    os.system(f"cd {project_name} && ./stop.sh")
    click.echo(f"Project {project_name} stopped! {COOL}")


@cli.command()
@click.argument("project_name")
def delete_project(project_name):
    """Delete an Airflow project"""
    if not os.path.exists(project_name):
        click.echo(f"Project {project_name} does not exist! {CONFUSED}")
        return

    click.echo(f"Deleting project {project_name}... {WORKING}")
    if delete.delete_proj(project_name):
        click.echo(f"Project {project_name} deleted! {COOL}")
    else:
        click.echo(f"Deletion of project {project_name} was cancelled or failed. {UNSATISFIED}")


@cli.command()
def delete_farm():
    """Delete the entire farm and all projects"""
    click.echo(f"Preparing to delete farm and all projects... {WORKING}")
    if delete.delete_farm():
        click.echo(f"Farm and selected projects deleted! {COOL}")
    else:
        click.echo(f"Deletion of farm was cancelled or failed. {UNSATISFIED}")


@cli.command()
def delete_all():
    """Delete all projects and the farm"""
    click.echo(f"Preparing to delete all projects and the farm... {WORKING}")
    if delete.delete_all():
        click.echo(f"All projects and the farm have been deleted! {COOL}")
    else:
        click.echo(f"Deletion process was cancelled or failed. {UNSATISFIED}")


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


if __name__ == "__main__":
    cli()
