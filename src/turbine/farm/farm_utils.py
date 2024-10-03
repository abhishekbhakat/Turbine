import logging
import os
import sys

logger = logging.getLogger(__name__)

# Kaomoji for added character
WORKING = "ᕦ(ò_óˇ)ᕤ"
YAY = "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
ANGRY = "(╯°□°）╯︵ ┻━┻"
CONFUSED = "(-_-;)・・・"
UNSATISFIED = "(－‸ლ)"
COOL = "(⌐■_■)"


def setup_logging(log_file_path):
    """Set up logging for the farm and projects"""
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(filename=log_file_path, level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # Add a stream handler to also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)


def redirect_output_to_log(log_file):
    """Redirect stdout and stderr to the log file"""
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    sys.stdout = open(log_file, "a")
    sys.stderr = open(log_file, "a")
