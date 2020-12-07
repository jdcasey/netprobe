from jinja2 import Environment, FileSystemLoader, PackageLoader, ChoiceLoader
import datetime
import os
import logging
from math import floor, ceil

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


def timestamp(seconds):
    return str(datetime.datetime.fromtimestamp(seconds))


def percent(val):
    if float(val) <= 1.0:
        return f"{round(float(float(val)*100))}%"
    else:
        return f"{round(float(val))}%"


def ljustify(val, cols):
    use_cols = int(cols)
    return f"{val}{' '*(use_cols-len(str(val)))}"


def cjustify(val, cols):
    use_cols = int(cols)
    return f"{' '*floor((use_cols-len(str(val)))/2)}{val}{' '*ceil((use_cols-len(str(val)))/2)}"


def rjustify(val, cols):
    use_cols = int(cols)
    return f"{' '*(use_cols-len(str(val)))}{val}"


env = Environment(
    enable_async=True,
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
    # loader=ChoiceLoader(
    #     [FileSystemLoader(get_config_location()), PackageLoader("netprobe")]
    # )
)

env.filters["timestamp"] = timestamp
env.filters["percent"] = percent
env.filters["rjustify"] = rjustify
env.filters["cjustify"] = cjustify
env.filters["ljustify"] = ljustify


async def format(template_name, data):
    template = env.get_template(template_name)
    return await template.render_async(data)
