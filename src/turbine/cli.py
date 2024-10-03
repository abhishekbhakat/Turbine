import json
import logging
import os
import sys

import click

from turbine.airflow_projects.project_utils import initialize_project_structure, start_project, stop_project, write_project_files
from turbine.cache import (
    add_project_to_cache,
    load_cache,
)
from turbine.farm.composer import get_or_create_farm
from turbine.farm.delete import delete_all_impl, delete_farm_impl, delete_proj
from turbine.farm.farm_utils import ANGRY, CONFUSED, COOL, UNSATISFIED, WORKING, YAY, redirect_output_to_log, setup_logging

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Turbine CLI for managing Airflow deployments"""
    pass


@cli.command()
def delete_farm():
    """Delete the entire farm and all projects"""
    if delete_farm_impl():
        logger.info(f"Farm and selected projects deleted! {COOL}")
    else:
        logger.error(f"Deletion of farm was cancelled or failed. {UNSATISFIED}")


@cli.command()
def delete_all():
    """Delete all projects"""
    confirmation = click.confirm("Are you sure you want to delete all projects? This action cannot be undone.", default=False)
    if not confirmation:
        logger.info("Deletion cancelled.")
        return

    if delete_all_impl():
        logger.info(f"All projects have been deleted! {COOL}")
    else:
        logger.error(f"Deletion process was cancelled or failed. {UNSATISFIED}")


@cli.command()
def init_farm():
    """Initialize the farm"""
    farm_log_file = os.path.join(os.getcwd(), "farm", "start.log")
    recreating = False
    if os.path.exists(os.path.dirname(farm_log_file)):
        if click.confirm("Farm already exists. Do you want to delete everything and create a new farm?", default=False):
            delete_all_impl()
            recreating = True
        else:
            logger.info("Keeping existing farm. Initialization cancelled.")
            return

    setup_logging(farm_log_file)
    logger.info("Initializing farm...")
    get_or_create_farm(recreating)
    logger.info(f"Farm initialized {COOL}")


@cli.command()
def create_airflow_project():
    """Create a new Airflow project"""
    # Ensure farm is initialized before creating a project
    if not os.path.exists("farm"):
        logger.info(f"Farm not initialized. Initializing farm... {WORKING}")
        get_or_create_farm()
        logger.info(f"Farm initialized {COOL}")

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

    tgt_folder_path = os.path.join(os.getcwd(), tgt_folder)
    if os.path.exists(tgt_folder_path):
        logger.error(f"Project {tgt_folder} already exists! {CONFUSED}")
        return

    try:
        setup_logging(os.path.join(tgt_folder_path, "start.log"))
        logger.info(f"Creating project {tgt_folder}... {WORKING}")

        initialize_project_structure(tgt_folder_path)

        webserver_port, flower_port, redisdb, network, db_name = write_project_files(tgt_folder_path, tgt_folder, cache, remote_logging, vault, code_server, airflow_type, docker_remote_con_id, docker_remote_base_folder)
    except Exception as e:
        logger.error(f"Failed to create project {tgt_folder}: {str(e)} {ANGRY}")
        return

    # Log project details
    project_data = {"type": airflow_type, "remote_logging": remote_logging, "vault": vault, "code_server": code_server, "redisdb": redisdb, "webserver": webserver_port, "flower": flower_port, "network": network, "db_name": db_name}
    add_project_to_cache(cache, tgt_folder, project_data)

    logger.info(f"Project {tgt_folder} created successfully! {YAY}")
    logger.info(f"Webserver port: {webserver_port}")
    logger.info(f"Flower port: {flower_port}")
    logger.info(f"Redis DB: {redisdb}")
    logger.info(f"Network: {network}")
    logger.info(f"Database name: {db_name}")


@cli.command()
@click.argument("project_name")
def start_airflow_project(project_name):
    """Start an Airflow project"""
    project_path = os.path.join(os.getcwd(), project_name)
    if not os.path.exists(project_path):
        logger.error(f"Project {project_name} does not exist! {CONFUSED}")
        return

    log_file = os.path.join(project_path, "start.log")
    redirect_output_to_log(log_file)
    logger.info(f"Starting project {project_name}... {WORKING}")
    if start_project(project_name):
        logger.info(f"Project {project_name} started! {COOL}")
    else:
        logger.error(f"Failed to start project {project_name}. {CONFUSED}")


@cli.command()
@click.argument("project_name")
def stop_airflow_project(project_name):
    """Stop an Airflow project"""
    logger.info(f"Stopping project {project_name}... {WORKING}")
    if stop_project(project_name):
        logger.info(f"Project {project_name} stopped! {COOL}")
    else:
        logger.error(f"Failed to stop project {project_name}. {CONFUSED}")


@cli.command()
@click.argument("project_name")
def delete_airflow_project(project_name):
    """Delete an Airflow project"""
    project_path = os.path.join(os.getcwd(), project_name)
    if not os.path.exists(project_path):
        logger.error(f"Project {project_name} does not exist! {CONFUSED}")
        return

    logger.info(f"Deleting project {project_name}... {WORKING}")
    if delete_proj(project_name):
        logger.info(f"Project {project_name} deleted! {COOL}")
    else:
        logger.error(f"Deletion of project {project_name} was cancelled or failed. {UNSATISFIED}")


@cli.command()
def list_airflow_projects():
    """List all Airflow projects"""
    cache_file = ".cache"
    if not os.path.exists(cache_file):
        logger.info(f"No projects found! {CONFUSED}")
        return

    with open(cache_file) as f:
        airflows = json.load(f)

    if not airflows:
        logger.info(f"No projects found! {CONFUSED}")
        return

    logger.info(f"Airflow projects: {COOL}")
    for project in airflows.keys():
        logger.info(f"- {project}")


if __name__ == "__main__":
    print(f"Debug: __main__ called with sys.argv = {sys.argv}", file=sys.stderr)
    cli(prog_name="turbine")
