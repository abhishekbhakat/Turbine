import json
import logging
import os
import shutil
import subprocess

import click

logger = logging.getLogger(__name__)


def delete_proj(project_name):
    if os.path.exists(project_name):
        confirmation = click.confirm(f"Are you sure you want to delete project {project_name}?", default=False)
        if not confirmation:
            logger.info("Project deletion cancelled.")
            return False

        shutil.rmtree(project_name)
        logger.info(f"Project {project_name} has been deleted.")

        # Remove project from cache and get the database name
        cache_file = ".cache"
        db_name = None
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cache = json.load(f)

            if project_name in cache:
                db_name = cache[project_name].get("db_name")
                del cache[project_name]

            with open(cache_file, "w") as f:
                json.dump(cache, f, indent=4)

            logger.info(f"Project {project_name} has been removed from the cache.")

        # Delete the project-specific database
        if db_name:
            try:
                subprocess.run(["docker", "run", "--rm", "--network", "airflow-network", "postgres:13", "psql", "-h", "postgres", "-U", "airflow", "-d", "airflow", "-c", f"DROP DATABASE IF EXISTS {db_name};"], check=True)
                logger.info(f"Database {db_name} has been deleted.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error deleting database {db_name}: {e}")
        return True
    else:
        logger.warning(f"Project {project_name} does not exist.")
        return False


def delete_farm_impl():
    farm_dir = "farm"
    if os.path.exists(farm_dir):
        confirmation = click.confirm("Are you sure you want to delete the farm? This will delete all projects and cannot be undone.", default=False)
        if not confirmation:
            logger.info("Farm deletion cancelled.")
            return False

        # Get all projects from cache
        cache_file = ".cache"
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cache = json.load(f)

            # Ask for confirmation for each project
            for project_name in list(cache.keys()):
                project_confirmation = click.confirm(f"Delete project {project_name}?", default=False)
                if project_confirmation:
                    delete_proj(project_name)
                else:
                    logger.info(f"Skipping deletion of project {project_name}.")

        # Delete the farm directory
        shutil.rmtree(farm_dir)
        logger.info("Farm has been deleted.")

        # Clear the cache
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info("Cache has been cleared.")

        return True
    else:
        logger.warning("Farm does not exist.")
        return False


def delete_all():
    confirmation = click.confirm("Are you sure you want to delete all projects? This action cannot be undone.", default=False)
    if not confirmation:
        logger.info("Deletion cancelled.")
        return False

    return delete_all_impl()


def delete_all_impl():
    """Delete all projects and the farm"""
    cache_file = ".cache"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)
        for project_name in list(cache.keys()):
            project_path = os.path.join(os.getcwd(), project_name)
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                logger.info(f"Deleted project: {project_name}")
        os.remove(cache_file)
        logger.info("Cache has been cleared.")
    return True
