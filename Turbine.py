import os, sys, stat, socket, json, shutil, platform
from templates import *

# check if the cache file exists
file_path = os.path.join(os.getcwd(), ".cache")
if not os.path.exists(file_path):
    print(f"Creating new cache{WORKING}")
    with open(file_path, "w") as f:
        json.dump({}, f, indent=4)


def write_farm(farm):
    with open(os.path.join(farm, "vault.Dockerfile"), "w") as f:
        f.write(VAULTDOCKER.format(farm))
    with open(os.path.join(farm, "vault.json"), "w") as f:
        f.write(VAULTJSON)
    with open(os.path.join(farm, "start.sh"), "w") as f:
        f.write(FARMSTART)
    with open(os.path.join(farm, "smtp.Dockerfile"), "w") as f:
        f.write(FARMSMTPDOCKER)
    with open(os.path.join(farm, "docker-compose.yml"), "w") as f:
        f.write(FARMCOMPOSE)
    with open(os.path.join(farm, "marquez.dev.yml"), "w") as f:
        f.write(MARQUEZCONF)
    with open(os.path.join(farm, "postgresql.conf"), "w") as f:
        f.write(MARQUEZPOSTGRESCONF)
    with open(os.path.join(farm, "redis.Dockerfile"), "w") as f:
        f.write(REDISDOCKERFILE)
    os.chmod(os.path.join(farm, "start.sh"), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)


def get_or_create_farm():
    farm = "farm"
    if not os.path.exists(farm):
        print(f"Creating new farm{WORKING}")
        os.makedirs(farm)
        os.makedirs(os.path.join(farm, "backups-s3"))
        os.makedirs(os.path.join(farm, "backups-gcs"))
        os.makedirs(os.path.join(farm, "backups-azure"))
        write_farm(farm)
        print(f"New farm created using network as 172.22.0.1/16! {YAY}")
    else:
        print(f"Updating farm{WORKING}")
        write_farm(farm)
        print(f"Updated farm using network as 172.22.0.1/16! {YAY}")


def update_cache(airflow: dict, airflow_type_str):
    airflow["type"] = airflow_type_str
    with open(".cache", "r") as f:
        airflows = json.load(f)
    airflows[tgt_folder] = airflow
    with open(".cache", "w") as f:
        json.dump(airflows, f, indent=4)
    print(f"Cache updated! {YAY}")


def get_or_create_cache(tgt_folder):
    try:
        with open(".cache", "r") as f:
            airflows = json.load(f)
    except FileNotFoundError:
        airflows = {}
        with open(".cache", "w") as f:
            json.dump(airflows, f)
    return airflows.get(tgt_folder)


def porter(init):
    result = 1
    for i in range(init, 65535):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", i))
        sock.close()
        if result != 0:
            break
    return i


def get_network():
    with open(".cache", "r") as f:
        airflows = json.load(f)
    used_network = {airflows[folder]["network"].split(".")[-1] for folder in airflows}
    net = next((i for i in range(2, 255) if str(i) not in used_network), 1)
    return f"172.22.{net}"


def get_redis():
    with open(".cache", "r") as f:
        airflows = json.load(f)
    used_redisdbs = {airflows[folder]["redisdb"] for folder in airflows}
    return next((i for i in range(1000) if i not in used_redisdbs), 0)


def get_webserver():
    with open(".cache", "r") as f:
        airflows = json.load(f)
    used_webserver = {airflows[folder]["webserver"] for folder in airflows}
    if not used_webserver:
        used_webserver.add(0)
    return porter(max(8080, max(used_webserver) + 1))


def get_flower():
    with open(".cache", "r") as f:
        airflows = json.load(f)
    used_flower = {airflows[folder]["flower"] for folder in airflows}
    if not used_flower:
        used_flower.add(0)
    return porter(max(5555, max(used_flower) + 1))


def get_code():
    with open(".cache", "r") as f:
        airflows = json.load(f)
    used_code = {airflows[folder]["code"] for folder in airflows}
    if not used_code:
        used_code.add(0)
    return porter(max(7000, max(used_code) + 1))


def create_folder_and_copy_utils(
    folder_name, remote_login=False, vault=False, code_server=False, airflow_type="1"
):
    web_p = get_webserver()
    flower_p = get_flower()
    code_p = get_code()
    network = get_network()
    redisdb = get_redis()
    print(
        f"Using port {str(web_p)} for webserver, {str(flower_p)} for flower, {str(code_p)} for IDE and {str(redisdb)} for redis"
    )
    print(f"Using network: {network}.1")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        if airflow_type == "1":
            os.system(f"cd {folder_name} && astro dev init")
        else:
            os.makedirs(os.path.join(folder_name, "dags"))
            os.makedirs(os.path.join(folder_name, "logs"))
            os.makedirs(os.path.join(folder_name, "plugins"))
    else:
        print("The folder already exists!")
        sys.exit()
    with open(os.path.join(folder_name, "Dockerfile"), "a") as f:
        f.write(
            DOCKERFILE.format(
                folder_name,
                redisdb,
                str(remote_login),
                "airflow.providers.hashicorp.secrets.vault.VaultBackend"
                if vault
                else "",
                arch
            )
        )
    with open(os.path.join(folder_name, "packages.txt"), "a") as f:
        f.write(PACKAGES)
    with open(os.path.join(folder_name, "docker-compose.yaml"), "w") as f:
        draft = (
            COMPOSE.format(folder_name, "${PWD}", COMPOSE_CODE if code_server else "")
            .replace("8080:8080", f"{str(web_p)}:8080")
            .replace("5555:5555", f"{str(flower_p)}:5555")
            .replace("7000:7000", f"{str(code_p)}:{str(code_p)}")
        )
        draft = draft.replace("172.22.0", network)
        f.write(draft)
    with open(os.path.join(folder_name, "start.sh"), "w") as f:
        f.write(
            START.format(folder_name)
            .replace("8080", str(web_p))
            .replace("5555", str(flower_p))
            .replace("7000", str(code_p))
        )
    with open(os.path.join(folder_name, "stop.sh"), "w") as f:
        f.write(STOP)
    with open(os.path.join(folder_name, "clean.sh"), "w") as f:
        f.write(CLEAN)
    with open(os.path.join(folder_name, "log.Dockerfile"), "w") as f:
        f.write(LOGDOCKERFILE)
    with open(os.path.join(folder_name, "logstash.conf"), "w") as f:
        f.write(LOGCONF.replace("filebeat", folder_name))
    with open(os.path.join(folder_name, "requirements.txt"), "a") as f:
        f.write(REQUIREMENTS)
    with open(os.path.join(folder_name, "code.Dockerfile"), "w") as f:
        f.write(CODEDOCKERFILE.replace("7000", str(code_p)))
    os.chmod(
        os.path.join(folder_name, "start.sh"),
        stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO,
    )
    os.chmod(
        os.path.join(folder_name, "stop.sh"), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
    )
    os.chmod(
        os.path.join(folder_name, "clean.sh"),
        stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO,
    )
    return {
        "webserver": web_p,
        "flower": flower_p,
        "code": code_p,
        "network": network,
        "redisdb": redisdb,
    }


def force_create_folder_and_copy_utils(folder_name):
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    airflow = create_folder_and_copy_utils(folder_name)
    update_cache(airflow)


def true_like(s):
    return s.lower()[0] == "y" if s else False


def check_platform():
    architechtures = {
        "x86_64": "amd64",
        "AMD64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv8l": "arm64",
    }
    if platform.system() == "Windows":
        print("Windows is not supported! {ANGRY}")
        sys.exit()
    arch = platform.machine()
    if arch not in architechtures:
        print(f"Unsupported architecture {arch}! {ANGRY}")
        sys.exit()
    return architechtures[arch]

arch = check_platform()
get_or_create_farm()
airflow_type = input(
    "Airflow type:\n 1. Astro [default]\n 2. OSS \n 3. OSS Main branch\n-> "
)
if airflow_type not in ["1", "2", "3", ""]:
    print(f"Invalid choice! {ANGRY}")
    sys.exit()
if airflow_type in ["1", ""]:
    DOCKERFILE = ASTRO_DOCKERFILE
    airflow_type_str = "astro"
elif airflow_type == "2":
    DOCKERFILE = OSS_DOCKERFILE
    airflow_type_str = "oss"
elif airflow_type == "3":
    DOCKERFILE = DEV_DOCKERFILE
    airflow_type_str = "oss_dev"
tgt_folder = input("Project name: ")
tgt_folder = f"{tgt_folder.lower()}-{airflow_type_str}-airflow"
REMOTE_LOGGING = true_like(input("Enable remote logging [yN]: "))
VAULT = true_like(input("Enable vault [yN]: "))
CODE_SERVER = true_like(input("Enable code server [yN]: "))
if not get_or_create_cache(tgt_folder):
    airflow = create_folder_and_copy_utils(
        tgt_folder, REMOTE_LOGGING, VAULT, CODE_SERVER, airflow_type
    )
    update_cache(airflow, airflow_type_str)
else:
    print(f"Name already used! {CONFUSED}")
    choice = input("overwrite [yN]:")
    if not choice:
        pass
    elif choice.lower()[0] == "y":
        force_create_folder_and_copy_utils(tgt_folder)
    print(f"Not updating! {UNSATISFIED}")
