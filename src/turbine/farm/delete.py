import logging
import os
import shutil

import click

logger = logging.getLogger(__name__)


def delete_proj(project_path):
    """Delete a specific project"""
    if click.confirm(f"Are you sure you want to delete the project at {project_path}?"):
        try:
            shutil.rmtree(project_path)
            logger.info(f"Project at {project_path} has been deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project at {project_path}. Error: {str(e)}")
            return False
    else:
        logger.info("Project deletion cancelled.")
        return False


def delete_farm_impl():
    """Delete the farm and all projects"""
    farm_path = os.path.join(os.getcwd(), "farm")
    if click.confirm("Are you sure you want to delete the farm and all projects?"):
        try:
            shutil.rmtree(farm_path)
            logger.info("Farm and all projects have been deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete farm. Error: {str(e)}")
            return False
    else:
        logger.info("Farm deletion cancelled.")
        return False


def delete_all_impl():
    """Delete all projects and the farm"""
    if click.confirm("Are you sure you want to delete all projects and the farm?"):
        try:
            for item in os.listdir(os.getcwd()):
                if item.endswith("-airflow"):
                    shutil.rmtree(os.path.join(os.getcwd(), item))
            farm_path = os.path.join(os.getcwd(), "farm")
            if os.path.exists(farm_path):
                shutil.rmtree(farm_path)
            logger.info("All projects and the farm have been deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete all projects and farm. Error: {str(e)}")
            return False
    else:
        logger.info("Deletion process cancelled.")
        return False
