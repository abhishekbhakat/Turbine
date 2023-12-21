import os
import shutil
import json
from templates import *

# check if the cache file exists
cache_path = os.path.join(os.getcwd(), ".cache")
if not os.path.exists(cache_path):
    print(f"Cache file not found! {ANGRY}")
    exit()


def delete_from_cache(tgt_folder):
    # update_cache
    with open(cache_path, "r") as f:
        airflows = json.load(f)
        try:
            airflows.pop(tgt_folder)
        except KeyError:
            print("Cache clean!")
            exit()  # This is needed or else script can delete any folder
    with open(cache_path, "w") as f:
        json.dump(airflows, f, indent=4)


def delete_proj(project):
    print(f"Deleting project: {project}")
    # tgt_folder = input("Enter the project to delete: ")
    tgt_path = os.path.join(os.getcwd(), project)
    # check if the project exists
    if not os.path.exists(tgt_path):
        print(f"Path not found! {CONFUSED}")
        delete_from_cache(project)
        exit()
    # if the tgt_folder is not a key in cache print not a project folder and exit
    with open(cache_path, "r") as f:
        airflows = json.load(f)
        if project not in airflows:
            print(f"Not a project folder! {OOPS}")
            exit()
    print(f"Checking project: {tgt_path}")
    # compose down the project first
    os.system(f"docker-compose -f {tgt_path}/docker-compose.yaml down")
    os.system(f"docker-compose -f {tgt_path}/docker-compose.yaml down -v")
    delete_from_cache(project)
    # delete the project folder
    shutil.rmtree(tgt_path)
    print(f"Project {project} deleted! {YAY}")

if __name__ == "__main__":
    # list all the projects
    with open(cache_path, "r") as f:
        airflows = json.load(f)
        if len(airflows) > 0:
            print("Projects found:")
            for id, airflow in enumerate(airflows):
                print(f" {id+1}. {airflow}")
        else:
            print(f"No projects found! {OOPS}")
    print(" 0. Exit")
    print("-1. Delete all projects")
    print("-2. Destroy everything")
    # ask for the project to delete
    choice = input("-> ")
    if choice in ["0", ""]:
        exit()
    try:
        choice = int(choice)
    except ValueError:
        print(f"Invalid choice! {ANGRY}")
        exit()
    if choice < -2 or choice > len(airflows):
        print(f"Invalid choice! {ANGRY}")
        exit()
    elif choice < 0:
        for project in airflows:
            delete_proj(project)
        if choice < -1:
            farm_path = os.path.join(os.getcwd(), 'farm')
            if os.path.exists(cache_path):
                os.system(f"docker-compose -f {farm_path}/docker-compose.yaml down")
                os.system(f"docker-compose -f {farm_path}/docker-compose.yaml down -v")
                shutil.rmtree(farm_path)
            os.remove('.cache')
            print(f"Destroyed everything! {SAYONARA}")
    elif choice > 0:
        delete_proj(airflows[choice-1])
