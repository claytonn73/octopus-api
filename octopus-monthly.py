#!/usr/bin/env python3
"""Gas usage from the Octopus API."""

import dotenv
import asyncio
import logging
import logging.handlers
import os

from dateutil import parser

from octopusapi.api import OctopusClient
from influxconnection import InfluxConnection


def get_logger():
    """Log messages to the syslog."""
    logger = logging.getLogger()
    handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_DAEMON, address='/dev/log')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    log_format = 'python[%(process)d]: [%(levelname)s] %(filename)s:%(funcName)s:%(lineno)d \"%(message)s\"'
    handler.setFormatter(logging.Formatter(fmt=log_format))
    return logger


def log_usage(usage, influxdb, influx_tags, measurement):
    """Load historical data into influxdb."""
    for data in usage:
        thetime = parser.parse(data['interval_start'])
        influx_fields = {
            'consumption': data['consumption'],
            'month': thetime.strftime("%b %Y")
        }
        influx_data = [
            {
                'measurement': measurement,
                'time': data['interval_start'],
                'tags': influx_tags,
                'fields': influx_fields,
            }
        ]
        influxdb.write_points(influx_data)


async def main():
    """Load historical data into influxdb."""
    global logger
    logger = get_logger()
    env = dotenv.dotenv_values(os.path.expanduser("~/.env"))

    with InfluxConnection() as connection:

        with OctopusClient(apikey=env['octopus_apikey'], account=env['octopus_account']) as client:

            # client.set_period_from("2020-07-01T00:00")
            # client.set_period_to("2021-08-01T00:00")
            client.set_page_size(90)
            client.set_group_by("month")
            influx_tags = {
                'account_number': client.get_account_number(),
            }
            logger.info("Adding Octopus Monthly Usage information to influxdb")
            usage = client.get_gas_consumption(ago=999, days=999)
            log_usage(usage, connection.influxdb, influx_tags, 'gas__monthly_consumption')

            usage = client.get_electricity_consumption(ago=999, days=999)
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_monthly_consumption')

            usage = client.get_electricity_export(ago=999, days=999)
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_monthly_export')

asyncio.run(main())
