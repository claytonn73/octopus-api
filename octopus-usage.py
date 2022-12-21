#!/usr/bin/env python3
"""Gas and Electricity usage from the Octopus API."""


import os
import asyncio
import logging
import logging.handlers
import dotenv

from dateutil import parser
from influxconnection import InfluxConnection

from octopusapi.api import OctopusClient


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
    """Load usage data into influxdb."""
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
    """Query historical data and load into influxdb."""
    logger = get_logger()
    env = dotenv.dotenv_values(os.path.expanduser("~/.env"))

    with InfluxConnection() as connection:
        with OctopusClient(apikey=env['octopus_apikey'], account=env['octopus_account']) as client:

            client.set_page_size(9999)
            client.set_group_by("day")
            influx_tags = {
                'account_number': client.get_account_number(),
            }

            logger.info("Adding Octopus Usage information to influxdb")
            usage = client.get_gas_consumption() 
            # usage = client.get_gas_consumption(intervals=365, ago=365, days=365)
            log_usage(usage, connection.influxdb, influx_tags, 'gas_consumption')

            usage = client.get_electricity_consumption()
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_consumption')

            usage = client.get_electricity_export()
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_export')

if __name__ == "__main__":

    asyncio.run(main())
