import os
import stat

from turbine.templates import FARM_COMPOSE_TEMPLATE, FARM_START_SCRIPT_TEMPLATE, FARM_STOP_SCRIPT_TEMPLATE, MARQUEZ_DEV_YAML_TEMPLATE, SMTP_DOCKERFILE_TEMPLATE, VAULT_DOCKERFILE_TEMPLATE, VAULT_JSON_TEMPLATE


def get_or_create_farm():
    farm = "farm"
    if not os.path.exists(farm):
        print("Creating new farm...")
        os.makedirs(farm)
        os.makedirs(os.path.join(farm, "backups-s3"))
        os.makedirs(os.path.join(farm, "backups-gcs"))
        os.makedirs(os.path.join(farm, "backups-azure"))
        write_farm(farm)
        print("New farm created using network as 172.27.0.1/16!")
    else:
        print("Updating farm...")
        write_farm(farm)
        print("Updated farm using network as 172.27.0.1/16!")


def write_farm(farm):
    # Write docker-compose.yaml for the farm
    with open(os.path.join(farm, "docker-compose.yaml"), "w") as f:
        f.write(FARM_COMPOSE_TEMPLATE)

    # Write vault.Dockerfile
    with open(os.path.join(farm, "vault.Dockerfile"), "w") as f:
        f.write(VAULT_DOCKERFILE_TEMPLATE)

    # Write vault.json
    with open(os.path.join(farm, "vault.json"), "w") as f:
        f.write(VAULT_JSON_TEMPLATE)

    # Write smtp.Dockerfile
    with open(os.path.join(farm, "smtp.Dockerfile"), "w") as f:
        f.write(SMTP_DOCKERFILE_TEMPLATE)

    # Write marquez.dev.yaml
    with open(os.path.join(farm, "marquez.dev.yaml"), "w") as f:
        f.write(MARQUEZ_DEV_YAML_TEMPLATE)

    # Write start.sh
    start_script_path = os.path.join(farm, "start.sh")
    with open(start_script_path, "w") as f:
        f.write(FARM_START_SCRIPT_TEMPLATE)
    os.chmod(start_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Write stop.sh
    stop_script_path = os.path.join(farm, "stop.sh")
    with open(stop_script_path, "w") as f:
        f.write(FARM_STOP_SCRIPT_TEMPLATE)
    os.chmod(stop_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    print(f"Farm files created in {farm} directory.")
