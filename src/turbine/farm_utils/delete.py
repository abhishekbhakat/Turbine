import json
import os
import shutil
import subprocess


def delete_proj(project_name):
    if os.path.exists(project_name):
        shutil.rmtree(project_name)
        print(f"Project {project_name} has been deleted.")

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

            print(f"Project {project_name} has been removed from the cache.")

        # Delete the project-specific database
        if db_name:
            try:
                subprocess.run(["docker", "run", "--rm", "--network", "airflow-network", "postgres:13", "psql", "-h", "postgres", "-U", "airflow", "-d", "airflow", "-c", f"DROP DATABASE IF EXISTS {db_name};"], check=True)
                print(f"Database {db_name} has been deleted.")
            except subprocess.CalledProcessError as e:
                print(f"Error deleting database {db_name}: {e}")
    else:
        print(f"Project {project_name} does not exist.")


def delete_farm():
    farm_dir = "farm"
    if os.path.exists(farm_dir):
        shutil.rmtree(farm_dir)
        print("Farm has been deleted.")
    else:
        print("Farm does not exist.")

    # Clear the cache
    cache_file = ".cache"
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Cache has been cleared.")
    else:
        print("Cache file does not exist.")


def delete_all():
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

    print("All projects and the farm have been deleted.")
