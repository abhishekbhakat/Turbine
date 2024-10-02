import json
import os
import re

CACHE_FILE = ".cache"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)


def get_next_available_port(start_port, used_ports):
    port = max(used_ports + [start_port - 1]) + 1
    while port in used_ports:
        port += 1
    return port


def get_next_webserver_port(cache):
    used_ports = [project["webserver"] for project in cache.values() if "webserver" in project]
    return get_next_available_port(8080, used_ports)


def get_next_flower_port(cache):
    used_ports = [project["flower"] for project in cache.values() if "flower" in project]
    return get_next_available_port(5555, used_ports)


def get_next_redis_db(cache):
    used_dbs = [project["redisdb"] for project in cache.values() if "redisdb" in project]
    return max(used_dbs + [-1]) + 1


def get_next_network(cache):
    used_networks = [project["network"].split(".")[-1] for project in cache.values() if "network" in project]
    used_networks = [int(net) for net in used_networks]
    net = next((i for i in range(2, 255) if i not in used_networks), 1)
    return f"172.27.{net}"


def generate_db_name(project_name):
    # Remove non-alphanumeric characters and convert to lowercase
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", project_name).lower()
    # Truncate to 63 characters (PostgreSQL limitation) and add 'db' suffix
    return f"{clean_name[:60]}db"


def add_project_to_cache(cache, project_name, project_data):
    cache[project_name] = project_data
    save_cache(cache)


def remove_project_from_cache(cache, project_name):
    if project_name in cache:
        del cache[project_name]
        save_cache(cache)


def get_project_from_cache(cache, project_name):
    return cache.get(project_name)
