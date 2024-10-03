import logging
import os
import stat

from turbine.cache import add_project_to_cache, generate_db_name, get_next_flower_port, get_next_network, get_next_redis_db, get_next_webserver_port

logger = logging.getLogger(__name__)


def initialize_project_structure(tgt_folder_path):
    """
    Initialize the basic project structure

    :param tgt_folder_path: Path to the target folder where the project structure will be created
    :return: None
    """
    directories = [
        tgt_folder_path,
        os.path.join(tgt_folder_path, "dags"),
        os.path.join(tgt_folder_path, "logs"),
        os.path.join(tgt_folder_path, "plugins"),
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            os.chmod(directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
            raise


def write_project_files(tgt_folder_path, tgt_folder, cache, remote_logging, vault, code_server, airflow_type, docker_remote_con_id, docker_remote_base_folder):
    """Write necessary files for the project"""
    from turbine.airflow_projects.dockerfile_templates import AIRFLOW_DOCKERFILE, CODE_SERVER_DOCKERFILE
    from turbine.airflow_projects.templates import PROJECT_DOCKER_COMPOSE_TEMPLATE, PROJECT_START_SCRIPT_TEMPLATE, PROJECT_STOP_SCRIPT_TEMPLATE

    webserver_port = get_next_webserver_port(cache)
    flower_port = get_next_flower_port(cache)
    redisdb = get_next_redis_db(cache)
    network = get_next_network(cache)
    db_name = generate_db_name(tgt_folder)

    # Write Dockerfile
    dockerfile_content = AIRFLOW_DOCKERFILE.format(
        project_name=tgt_folder,
        redisdb=redisdb,
        remote_login=str(remote_logging).lower(),
        vault_backend='"airflow.providers.hashicorp.secrets.vault.VaultBackend"' if vault else '""',
        arch="amd64",  # You might want to make this dynamic based on the system architecture
        docker_remote_con_id=docker_remote_con_id,
        docker_remote_base_folder=docker_remote_base_folder,
    )
    with open(os.path.join(tgt_folder_path, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

    # Write project-specific docker-compose.yaml
    docker_compose_content = PROJECT_DOCKER_COMPOSE_TEMPLATE.format(tgt_folder=tgt_folder, db_name=db_name, redisdb=redisdb, webserver_port=webserver_port, flower_port=flower_port)
    with open(os.path.join(tgt_folder_path, "docker-compose.yaml"), "w") as f:
        f.write(docker_compose_content)

    # Write start.sh
    start_script_content = PROJECT_START_SCRIPT_TEMPLATE.format(db_name=db_name, tgt_folder=tgt_folder, webserver_port=webserver_port, flower_port=flower_port)
    start_script_path = os.path.join(tgt_folder_path, "start.sh")
    with open(start_script_path, "w") as f:
        f.write(start_script_content)
    os.chmod(start_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Write stop.sh
    stop_script_content = PROJECT_STOP_SCRIPT_TEMPLATE.format(tgt_folder=tgt_folder)
    stop_script_path = os.path.join(tgt_folder_path, "stop.sh")
    with open(stop_script_path, "w") as f:
        f.write(stop_script_content)
    os.chmod(stop_script_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    if code_server:
        code_dockerfile_content = CODE_SERVER_DOCKERFILE.format(code_p=8080)  # You may want to dynamically assign this port
        with open(os.path.join(tgt_folder_path, "code.Dockerfile"), "w") as f:
            f.write(code_dockerfile_content)

    # Update cache
    project_data = {"type": airflow_type, "remote_logging": remote_logging, "vault": vault, "code_server": code_server, "redisdb": redisdb, "webserver": webserver_port, "flower": flower_port, "network": network, "db_name": db_name}
    add_project_to_cache(cache, tgt_folder, project_data)

    return webserver_port, flower_port, redisdb, network, db_name


def start_project(project_name):
    """Start an Airflow project"""
    project_path = os.path.join(os.getcwd(), project_name)
    if not os.path.exists(project_path):
        logger.error(f"Project {project_name} does not exist!")
        return False
    os.system(f"cd {project_path} && ./start.sh")
    return True


def stop_project(project_name):
    """Stop an Airflow project"""
    project_path = os.path.join(os.getcwd(), project_name)
    if not os.path.exists(project_path):
        logger.error(f"Project {project_name} does not exist!")
        return False
    os.system(f"cd {project_path} && ./stop.sh")
    return True
