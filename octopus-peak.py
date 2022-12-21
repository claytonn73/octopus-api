#!/usr/bin/env python3
"""Get peak and offpeak usage from octopus API."""

import asyncio
import logging
import logging.handlers
import sys
import os
import argparse
import dateutil
import dotenv
from datetime import datetime
from octopusapi.api import OctopusClient
from influxconnection import InfluxConnection


def get_logger():
    """Log message to sysout."""
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.ERROR)
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
    for data in usage:
        influx_fields = {
            'peak consumption': data['peak'],
            'offpeak consumption': data['offpeak'],
            'month': data['interval_start'].strftime("%b %Y")
        }
        influx_data = [
            {
                'measurement': measurement,
                'time': data['interval_start'].strftime("%m/%d/%Y"),
                'tags': influx_tags,
                'fields': influx_fields,
            }
        ]
        influxdb.write_points(influx_data)


async def main(reset):
    """Query historyical data and output peak and offpeak usage by day."""
    global logger
    logger = get_logger()
    env = dotenv.dotenv_values(os.path.expanduser("~/.env"))

    with InfluxConnection() as connection:
        if reset is True:
            connection.influxdb.drop_database('octopus')
            connection.influxdb.create_database('octopus')
            connection.influxdb.switch_database('octopus')

        with OctopusClient(apikey=env['octopus_apikey'], account=env['octopus_account']) as client:
            # client.set_period_from("2020-07-01T00:00")
            # client.set_period_to("2021-08-01T00:00")
            client.set_page_size(25000)
            # client.set_group_by("hour")
            influx_tags = {
                'account_number': client.get_account_number(),
            }
            # Query from the beginning of last month
            now = datetime.now()
            lastmonth = datetime(now.year, now.month - 1, 1).date()
            querydays = (now.date()-lastmonth).days
            if reset is True:
                querydays = 365
            if querydays > 0:
                usage = client.get_electricity_consumption(
                    intervals=25000, ago=querydays, days=querydays)
                # usage = client.get_electricity_consumption(intervals=25000, ago=365, days=365)
                daily = {}
                monthly = {}
                if usage is not None:
                    for entry in usage:
                        start = dateutil.parser.parse(entry["interval_start"])
                        time = start.time()
                        thedate = start.date()
                        themonth = datetime(start.year, start.month, 1).date()
                        if daily.get(thedate) is None:
                            daily[thedate] = {}
                            daily[thedate]["month"] = themonth
                            daily[thedate]["peak"] = 0
                            daily[thedate]["offpeak"] = 0
                        if monthly.get(themonth) is None:
                            monthly[themonth] = {}
                            monthly[themonth]["peak"] = 0
                            monthly[themonth]["offpeak"] = 0
                        kwh = entry["consumption"]
                        if time < datetime.strptime('00:15:00', '%H:%M:%S').time():
                            daily[thedate]["peak"] += round(kwh, 3)
                            monthly[themonth]["peak"] += round(kwh, 3)
                        elif time > datetime.strptime('04:15:00', '%H:%M:%S').time():
                            daily[thedate]["peak"] += round(kwh, 3)
                            monthly[themonth]["peak"] += round(kwh, 3)
                        else:
                            daily[thedate]["offpeak"] += round(kwh, 3)
                            monthly[themonth]["offpeak"] += round(kwh, 3)
                theusage = []
                for date in daily:
                    dict = {}
                    dict["interval_start"] = date
                    dict["peak"] = round(daily[date]["peak"], 2)
                    dict["offpeak"] = round(daily[date]["offpeak"], 2)
                    theusage.append(dict)
                log_usage(theusage, connection.influxdb, influx_tags,
                          'electricity_peak_offpeak_daily')
                theusage = []
                for date in monthly:
                    dict = {}
                    dict["interval_start"] = date
                    dict["peak"] = round(monthly[date]["peak"], 2)
                    dict["offpeak"] = round(monthly[date]["offpeak"], 2)
                    theusage.append(dict)
                log_usage(theusage, connection.influxdb, influx_tags,
                          'electricity_peak_offpeak_monthly')


if __name__ == "__main__":

    args = getopts(sys.argv[1:])

    asyncio.run(main(args.reset))
