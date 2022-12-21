#!/usr/bin/env python3
"""Get peak and offpeak usage from octopus API."""

import asyncio
import logging
import logging.handlers
import sys
import os
import dateutil
import dotenv
from datetime import datetime
from octopusapi.api import OctopusClient


def get_logger():
    """Log message to sysout."""
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)
    return logger


async def main():
    """Query historyical data and output peak and offpeak usage by day."""
    global logger
    logger = get_logger()
    env = dotenv.dotenv_values(os.path.expanduser("~/.env"))

    with OctopusClient(apikey=env['octopus_apikey'], account=env['octopus_account']) as client:
        # client.set_period_from("2020-07-01T00:00")
        # client.set_period_to("2021-08-01T00:00")
        client.set_page_size(9999)
        # client.set_group_by("hour")

        client.print_api_response("Account")


if __name__ == "__main__":
    asyncio.run(main())
