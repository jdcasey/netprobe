from ruamel.yaml import YAML
import logging
from os.path import dirname

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

IP_REFLECTOR = "myip-url"

WIFI_DEVICE = "wifi-device"
DEFAULT_WIFI_DEVICE = "wlan0"

REPORTER_TIMEOUT = "report-period-secs"
DEFAULT_REPORTER_TIMEOUT = 300

TELEGRAM_SESSION_ID = "telegram-session-id"
TELEGRAM_API_ID = "telegram-api-id"
TELEGRAM_API_HASH = "telegram-api-hash"
NODE_NAME = "telegram-node-name"

WRITER_COUNT = "writers"
DEFAULT_WRITER_COUNT = 2

ANNOUNCE_START = 'announce-on-start'
DEFAULT_ANNOUNCE_START = False

config = dict()
config_location = None


def load_config(config_file):
    global config, config_location

    logging.info(f"Loading configuration from: {config_file}")
    config.clear()
    with open(config_file) as f:
        config = YAML(typ="safe").load(f)
        config_location = dirname(config_file)


def get_config(key):
    global config
    return config.get(key) or None


def get_config_location():
    return config_location
