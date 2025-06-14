import os
import yaml
from pathlib import Path
import template_raya_package.tools.color_print as cp

def load_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) # Usa safe_load para mayor seguridad
    except FileNotFoundError:
        cp.abort(f"Configuration file not found in '{config_path}'")

PATH_CONFIG = Path(os.environ["ROBOT_CONFIG_PATH"]) / "manager" / "manager.config.yaml"
GREENGRASS_CONFIG_FILE_PATH = '/greengrass/v2/config/effectiveConfig.yaml'

CONFIG_DICT = load_config(PATH_CONFIG)
try:
    GREENGRASS_CONFIG = load_config(GREENGRASS_CONFIG_FILE_PATH)
    ROBOT_NAME = GREENGRASS_CONFIG.get('system',{}).get('thingName')
except Exception as e:
    cp.abort(
        f"Not possible to read the file '{GREENGRASS_CONFIG_FILE_PATH}'\n"
        f"[{type(e)}]: {e}"
    )

AWS_ACCESS_KEY_ID = CONFIG_DICT.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = CONFIG_DICT.get("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = CONFIG_DICT.get("AWS_DEFAULT_REGION")

ROSBAGS_BUCKET = CONFIG_DICT.get("CONFIG_BUCKET", "ur-rosbags-logs")
PATH_ROSBAGS = CONFIG_DICT.get("CONFIG_BUCKET", "/robot/generic_persistent_data/rosbag")
PATH_LOGS = CONFIG_DICT.get("CONFIG_BUCKET", "/robot/generic_persistent_data/logs")

ROBOT_ID = os.environ.get("ROBOT_ID")

print(f'ROBOT_ID: {ROBOT_ID}')