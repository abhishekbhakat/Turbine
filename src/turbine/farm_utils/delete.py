import json
import os
import shutil
import subprocess

import click


def delete_proj(project_name):
    if os.path.exists(project_name):
        confirmation = click.confirm(f"Are you sure you want to delete project {project_name}?", default=False)
        if not confirmation:
            click.echo("Project deletion cancelled.")
            return False

        shutil.rmtree(project_name)
        click.echo(f"Project {project_name} has been deleted.")

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

            click.echo(f"Project {project_name} has been removed from the cache.")

        # Delete the project-specific database
        if db_name:
            try:
                subprocess.run(["docker", "run", "--rm", "--network", "airflow-network", "postgres:13", "psql", "-h", "postgres", "-U", "airflow", "-d", "airflow", "-c", f"DROP DATABASE IF EXISTS {db_name};"], check=True)
                click.echo(f"Database {db_name} has been deleted.")
            except subprocess.CalledProcessError as e:
                click.echo(f"Error deleting database {db_name}: {e}")
        return True
    else:
        click.echo(f"Project {project_name} does not exist.")
        return False


def delete_farm():
    farm_dir = "farm"
    if os.path.exists(farm_dir):
        confirmation = click.confirm("Are you sure you want to delete the farm? This will delete all projects and cannot be undone.", default=False)
        if not confirmation:
            click.echo("Farm deletion cancelled.")
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
                    click.echo(f"Skipping deletion of project {project_name}.")

        # Delete the farm directory
        shutil.rmtree(farm_dir)
        click.echo("Farm has been deleted.")

        # Clear the cache
        if os.path.exists(cache_file):
            os.remove(cache_file)
            click.echo("Cache has been cleared.")

        return True
    else:
        click.echo("Farm does not exist.")
        return False


def delete_all():
    confirmation = click.confirm("Are you sure you want to delete all projects and the farm? This action cannot be undone.", default=False)
    if not confirmation:
        click.echo("Deletion cancelled.")
        return False

    # Get all projects from cache
    cache_file = ".cache"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache = json.load(f)

        # Delete each project
        for project_name in list(cache.keys()):
            delete_proj(project_name)

    # Delete the farm
    delete_farm()

    click.echo("All projects and the farm have been deleted.")
    return True
