#!/usr/bin/env python3
"""Get peak and offpeak usage from octopus API."""

import argparse
import asyncio
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timedelta

import dateutil.parser
from dotenv import dotenv_values
from dateutil.relativedelta import relativedelta

from influxconnection import InfluxConnection
from octopusapi.api import OctopusClient


def get_logger():
    """Log message to sysout."""
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.WARN)
    return logger


def getopts(argv):
    """Get arguments for this script."""
    parser = argparse.ArgumentParser(
        description='Query Powerwall usage')
    parser.add_argument('-r', '--reset', required=False, type=bool,
                        default=False, help='Reset database contents')
    args = parser.parse_args()

    return args


def log_usage(usage, influxdb, influx_tags, measurement):
    """Load historical data into influxdb."""
    influx_fields = {}
    for data in usage:
        if usage[data].get("Standard") is not None:
            influx_fields.update({'standard consumption': float(round(usage[data]['Standard'], 2))})
        if usage[data].get("Peak") is not None:
            influx_fields.update({'peak consumption': float(round(usage[data]['Peak'], 2))})
        if usage[data].get("OffPeak") is not None:
            influx_fields.update({'offpeak consumption': float(round(usage[data]['OffPeak'], 2))})
        influx_fields.update({'month': dateutil.parser.parse(data).strftime("%b %Y")})
        influx_data = [
            {
                'measurement': measurement,
                'time': dateutil.parser.parse(data).strftime("%m/%d/%Y"),
                'tags': influx_tags,
                'fields': influx_fields,
            }
        ]
        influxdb.write_points(influx_data)


async def main(reset):
    """Query historyical data and output peak and offpeak usage by day."""
    global logger
    logger = get_logger()
    env_path = os.path.expanduser('~/.env')
    if os.path.exists(env_path):
        env = dotenv_values(env_path)

    with InfluxConnection() as connection:
        if reset is True:
            connection.influxdb.drop_database('octopus')
            connection.influxdb.create_database('octopus')
            connection.influxdb.switch_database('octopus')

        with OctopusClient(apikey=env.get('octopus_apikey'), account=env.get('octopus_account')) as client:
            # client.set_period_from("2020-07-01T00:00")
            # client.set_period_to("2021-08-01T00:00")
            client.set_page_size(25000)
            # client.set_group_by("hour")
            influx_tags = {
                'account_number': client.account_number,
            }
            # Query from the beginning of last month
            now = datetime.now()
            monthsago = 0
            lastmonth = datetime(now.year, now.month, 1)-timedelta(days=1) + relativedelta(months=-monthsago)
            # lastmonth = datetime(now.year, now.month, 1)-timedelta(days=1)-timedelta(months=monthsago)
            firstofmonth = datetime(lastmonth.year, lastmonth.month, 1).date()
            querydays = (lastmonth.date()-firstofmonth).days
            startday = (now.date()-firstofmonth).days
            if reset is True:
                querydays = 365
            if querydays > 0:
                usage = client.get_electricity_consumption_byrange(
                    ago=startday, days=startday, daily=False)
                log_usage(usage, connection.influxdb, influx_tags,
                          'electricity_peak_offpeak_monthly')
                usage = client.get_electricity_consumption_byrange(
                    ago=startday, days=startday, daily=True)
                log_usage(usage, connection.influxdb, influx_tags,
                          'electricity_peak_offpeak_daily')

if __name__ == "__main__":
    args = getopts(sys.argv[1:])
    asyncio.run(main(args.reset))
