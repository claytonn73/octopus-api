#!/usr/bin/env python3
"""Electricity costs and gain from the Octopus API."""

import os
import asyncio
import logging
import logging.handlers
from datetime import datetime
import dotenv

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


async def main():
    """Load historical data into influxdb."""
    global logger
    logger = get_logger()
    env = dotenv.dotenv_values(os.path.expanduser("~/.env"))

    with InfluxConnection() as connection:

        with OctopusClient(apikey=env['octopus_apikey'], account=env['octopus_account']) as client:

            # client.set_period_from("2021-07-01T00:00")
            # client.set_period_to("2021-08-01T00:00")
            client.set_page_size(25000)
            charge = client.get_standing_charge()
            influx_tags = {
                'account_number': client.get_account_number(),
            }
            logger.info("Adding Octopus Cost information to influxdb")
            # Obtain half hour cost figures and add to influxdb
            cost = client.calculate_electricity_cost(30)
            for day in cost:
                cost[day] = int(cost[day] + charge)
                influx_fields = {
                    'cost': cost[day],
                    'month': day.strftime("%b %Y")
                }
                influx_data = [
                    {
                        'measurement': 'daily_electricity_cost',
                        'time': datetime.strftime(day, '%Y-%m-%dT%H:%MZ'),
                        'tags': influx_tags,
                        'fields': influx_fields,
                    }
                ]
                connection.influxdb.write_points(influx_data)

            # Obtain half hour gain figures and add to influxdb
            gain = client.calculate_electricity_gain(30)
            for day in gain:
                influx_fields = {
                    'gain': int(gain[day]),
                    'month': day.strftime("%b %Y")
                }
                influx_data = [
                    {
                        'measurement': 'daily_export_gain',
                        'time': datetime.strftime(day, '%Y-%m-%dT%H:%MZ'),
                        'tags': influx_tags,
                        'fields': influx_fields,
                    }
                ]
                connection.influxdb.write_points(influx_data)

asyncio.run(main())
