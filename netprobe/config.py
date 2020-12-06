from ruamel.yaml import YAML
import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)

IP_REFLECTOR = "myip-url"

REPORTER_TIMEOUT = "report-period-secs"
DEFAULT_REPORTER_TIMEOUT = 300

TELEGRAM_SESSION_ID = "telegram-session-id"
TELEGRAM_API_ID = "telegram-api-id"
TELEGRAM_API_HASH = "telegram-api-hash"
TELEGRAM_NODE_NAME = "telegram-node-name"

config = dict()


def load_config(config_file):
    global config

    logging.info(f"Loading configuration from: {config_file}")
    config.clear()
    with open(config_file) as f:
        config = YAML(typ="safe").load(f)


def get_config(key):
    global config
    return config.get(key) or None
