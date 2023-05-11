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
tgt_folder = input("Enter the project to delete: ")
tgt_path = os.path.join(os.getcwd(), tgt_folder)
#check if the project exists
if not os.path.exists(tgt_path):
    print("Path not found!")
    delete_from_cache(tgt_folder)
    exit()
#if the tgt_folder is not a key in cache print not a project folder and exit
with open(".cache", "r") as f:
    airflows = json.load(f)
    if tgt_folder not in airflows:
        print("Not a project folder!")
        exit()
print(f"Checking project: {tgt_path}")
#compose down the project first
os.system(f"docker-compose -f {tgt_path}/docker-compose.yaml down")
delete_from_cache(tgt_folder)
#delete the project folder
shutil.rmtree(tgt_path)