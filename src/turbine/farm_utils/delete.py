import os
import shutil
import json

def delete_proj(project_name):
    if os.path.exists(project_name):
        shutil.rmtree(project_name)
        print(f"Project {project_name} has been deleted.")
        
        # Remove project from cache
        cache_file = ".cache"
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
            
            if project_name in cache:
                del cache[project_name]
                
            with open(cache_file, "w") as f:
                json.dump(cache, f, indent=4)
            
            print(f"Project {project_name} has been removed from the cache.")
    else:
        print(f"Project {project_name} does not exist.")

def delete_farm():
    # Delete all projects
    cache_file = ".cache"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
        
        for project_name in list(cache.keys()):
            delete_proj(project_name)
    
    # Delete the farm directory
    farm_dir = "farm"
    if os.path.exists(farm_dir):
        shutil.rmtree(farm_dir)
        print("Farm has been deleted.")
    else:
        print("Farm does not exist.")

    # Clear the cache
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Cache has been cleared.")
    else:
        print("Cache file does not exist.")

def delete_all(confirm=True):
    if confirm:
        confirmation = input("Are you sure you want to delete all projects and the farm? (y/N): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled.")
            return

    delete_farm()
    print("All projects and the farm have been deleted.")