#!/usr/bin/env python3
"""Retrieve gas usage data from the Octopus API and logs it into an InfluxDB database."""

from datetime import datetime

from octopusapi.api import OctopusClient
from utilities import InfluxConnection, get_env, get_logger

logger = get_logger(destination="stdout",level="DEBUG")

def log_usage(usage, influxdb, account_number, measurement) -> None:
    """Load historical data into influxdb.
    Args:
        usage: The usage data to be logged.
        influxdb: The InfluxDB connection.
        account_number: The account number associated with the data.
        measurement: The measurement name for the data.
    """
    influx_data = [
        {
            "measurement": measurement,
            "time": data.interval_start.strftime("%Y-%m-%dT%H:%MZ"),
            "tags": {
                "account_number": account_number,
                "year": datetime.strftime(getattr(data, "interval_start"), "%Y"),
                "month": datetime.strftime(getattr(data, "interval_start"), "%Y %m"),
            },
            "fields": {"consumption": data.consumption},
        }
        for data in usage
        if data.interval_start.strftime("%d") == "01"
    ]
    logger.info("Adding  Octopus monthly usage information to influxdb")
    influxdb.write_points(influx_data)


def main() -> None:  # sourcery skip: extract-method
    """Query the octopus API to get monthly consumption and load data into influxdb."""

    env = get_env()
    with InfluxConnection(database="octopus", reset=False).connect() as connection:
        with OctopusClient(apikey=env.get("octopus_apikey"), account=env.get("octopus_account")) as client:
            client.set_page_size(9999)
            client.set_group_by("month")
            log_usage(
                client.get_electricity_consumption(ago=365, days=365),
                connection,
                client.account_number,
                "electricity_monthly_consumption",
            )
            log_usage(
                client.get_electricity_export(ago=365, days=365),
                connection,
                client.account_number,
                "electricity_monthly_export",
            )
            log_usage(
                client.get_gas_consumption(ago=365, days=365),
                connection,
                client.account_number,
                "gas__monthly_consumption",
            )


if __name__ == "__main__":
    main()
