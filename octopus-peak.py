#!/usr/bin/env python3
"""Get peak and offpeak usage from octopus API."""

import argparse
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from octopusapi.api import OctopusClient
from utilities import InfluxConnection, get_env, get_logger

logger = get_logger(destination="syslog", level="INFO")


def getopts():
    """Get arguments for this script."""
    parser = argparse.ArgumentParser(description="Log Octopus usage by cost category")
    parser.add_argument(
        "-r",
        "--reset",
        required=False,
        type=bool,
        default=False,
        help="Reset database contents",
    )
    return parser.parse_args()


def log_usage(usage, influxdb, account_number, measurement) -> None:
    """Load historical data into influxdb."""
    influx_data = []
    for data in usage:
        influx_fields = {}
        if usage[data].get("Standard"):
            influx_fields["standard consumption"] = float(round(usage[data]["Standard"], 2))
        if usage[data].get("Peak"):
            influx_fields.update({"peak consumption": float(round(usage[data]["Peak"], 2))})
        if usage[data].get("OffPeak"):
            influx_fields.update({"offpeak consumption": float(round(usage[data]["OffPeak"], 2))})
        influx_data.append(
            {
                "measurement": measurement,
                "time": datetime.strftime(data, "%Y-%m-%dT%H:%MZ"),
                "tags": {
                    "account_number": account_number,
                    "year": data.strftime("%Y"),
                    "month": data.strftime("%Y %m"),
                },
                "fields": influx_fields,
            }
        )
    logger.info("Adding  Octopus peak usage information to influxdb")
    influxdb.write_points(influx_data)


def main() -> None:
    """Query historyical data and output peak and offpeak usage by day."""

    env = get_env()
    args = getopts()
    with InfluxConnection(database="octopus", reset=args.reset).connect() as connection:
        with OctopusClient(apikey=env.get("octopus_apikey"), account=env.get("octopus_account")) as client:
            client.set_page_size(25000)
            # Query from the beginning of last month
            now = datetime.now()
            monthsago = 0
            lastmonth = datetime(now.year, now.month, 1) - timedelta(days=1) + relativedelta(months=-monthsago)
            firstofmonth = datetime(lastmonth.year, lastmonth.month, 1).date()
            querydays = (lastmonth.date() - firstofmonth).days
            startday = (now.date() - firstofmonth).days
            if args.reset is True:
                querydays = 365
            if querydays > 0:
                usage = client.get_electricity_consumption_byrange(ago=startday, days=startday, daily=False)
                log_usage(usage, connection, client.account_number, "electricity_peak_offpeak_monthly")
                usage = client.get_electricity_consumption_byrange(ago=startday, days=startday, daily=True)
                log_usage(usage, connection, client.account_number, "electricity_peak_offpeak_daily")


if __name__ == "__main__":
    main()
