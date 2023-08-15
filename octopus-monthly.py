#!/usr/bin/env python3
"""Gas usage from the Octopus API."""

from dotenv import dotenv_values
import asyncio
import logging
import logging.handlers
import os

from octopusapi.api import OctopusClient
from influxconnection import InfluxConnection


def get_logger():
    """Log messages to the syslog."""
    logger = logging.getLogger()
    handler = logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_DAEMON, address='/dev/log')
    logger.setLevel(logging.WARN)
    logger.addHandler(handler)
    # logger.addHandler(logging.StreamHandler(sys.stdout))
    log_format = 'python[%(process)d]: [%(levelname)s] %(filename)s:%(funcName)s:%(lineno)d \"%(message)s\"'
    handler.setFormatter(logging.Formatter(fmt=log_format))
    return logger


def log_usage(usage, influxdb, influx_tags, measurement):
    """Load historical data into influxdb."""
    for data in usage:
        # Only import data for which we have a full month
        if data.interval_start.strftime("%d") == "01":
            influx_fields = {
                'consumption': data.consumption,
                'month': data.interval_start.strftime("%b %Y")
            }
            influx_data = [
                {
                    'measurement': measurement,
                    'time': data.interval_start.strftime("%Y-%m-%dT%H:%MZ"),
                    'tags': influx_tags,
                    'fields': influx_fields,
                }
            ]
            influxdb.write_points(influx_data)


async def main():
    """Load historical data into influxdb."""
    global logger
    logger = get_logger()

    env_path = os.path.expanduser('~/.env')
    if os.path.exists(env_path):
        env = dotenv_values(env_path)
    with InfluxConnection() as connection:
        with OctopusClient(apikey=env.get('octopus_apikey'), account=env.get('octopus_account')) as client:
            client.set_page_size(9999)
            client.set_group_by("month")
            influx_tags = {
                'account_number': client.account_number,
            }
            logger.info("Adding Octopus Monthly Usage information to influxdb")
            usage = client.get_electricity_consumption(ago=365, days=365)
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_monthly_consumption')

            usage = client.get_electricity_export(ago=365, days=365)
            log_usage(usage, connection.influxdb, influx_tags, 'electricity_monthly_export')

            usage = client.get_gas_consumption(ago=365, days=365)
            log_usage(usage, connection.influxdb, influx_tags, 'gas__monthly_consumption')

asyncio.run(main())
