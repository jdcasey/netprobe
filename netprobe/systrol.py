import asyncio
import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


async def reboot():
    process = await asyncio.create_subprocess_shell(
        "/usr/sbin/reboot",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    output, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(
            f"Failed to reboot: {stderr.decode('utf-8').strip()}"
        )
        return "Command failed."
    else:
        return output.decode("utf-8")


async def list_packages():
    process = await asyncio.create_subprocess_shell(
        "/usr/bin/env pip list",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    pip_output, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(
            f"Failed to read installed packages: {stderr.decode('utf-8').strip()}"
        )
        return "Command failed."
    else:
        return pip_output.decode("utf-8")


async def upgrade_packages():
    process = await asyncio.create_subprocess_shell(
        "/usr/bin/env pip install --upgrade --progress-bar off netprobe",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    pip_output, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error(
            f"Failed to read installed packages: {stderr.decode('utf-8').strip()}"
        )
        return "Command failed."
    else:
        return pip_output.decode("utf-8")

