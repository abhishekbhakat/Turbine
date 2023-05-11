import os
import shutil
import json

def delete_from_cache(tgt_folder):
    #update_cache
    with open(".cache", "r") as f:
        airflows = json.load(f)
        try:
            airflows.pop(tgt_folder)
        except KeyError:
            print("Cache clean!")
            exit() # This is needed or else script can delete any folder
    with open(".cache", "w") as f:
        json.dump(airflows, f, indent=4)

#check if the cache file exists
if not os.path.exists(".cache"):
    print("Cache file not found!")
    exit()

#list all the projects
with open(".cache", "r") as f:
    airflows = json.load(f)
    if len(airflows) == 0:
        print("No projects found!")
        exit()
    print("Projects found:")
    for id,airflow in enumerate(airflows):
        print(f"{id+1}. {airflow}")
print("0. Exit")
#ask for the project to delete
choice = input("Enter the project to delete [0]: ")
if choice in ["0", ""]:
    exit()
try:
    choice = int(choice)
except ValueError:
    print("Invalid choice!")
    exit()
if choice < 0 or choice > len(airflows):
    print("Invalid choice!")
    exit()

project = list(airflows.keys())[choice-1]
print(f"Deleting project: {project}")


# tgt_folder = input("Enter the project to delete: ")
tgt_path = os.path.join(os.getcwd(), project)
#check if the project exists
if not os.path.exists(tgt_path):
    print("Path not found!")
    delete_from_cache(project)
    exit()
#if the tgt_folder is not a key in cache print not a project folder and exit
with open(".cache", "r") as f:
    airflows = json.load(f)
    if project not in airflows:
        print("Not a project folder!")
        exit()
print(f"Checking project: {tgt_path}")
#compose down the project first
os.system(f"docker-compose -f {tgt_path}/docker-compose.yaml down")
delete_from_cache(project)
#delete the project folder
shutil.rmtree(tgt_path)