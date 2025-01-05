#!/usr/bin/env python3
"""Gas and Electricity usage from the Octopus API."""

from octopusapi.api import OctopusClient
from utilities import InfluxConnection, get_env, get_logger

logger = get_logger(destination="syslog")


def log_usage(usage, influxdb, account_number, measurement) -> None:
    """Load usage data into influxdb."""
    influx_data = [
        {
            "measurement": measurement,
            "time": data.interval_start.strftime("%Y-%m-%dT%H:%MZ"),
            "tags": {
                "account_number": account_number,
                "month": data.interval_start.strftime("%Y %m"),
                "year": data.interval_start.strftime("%Y"),
            },
            "fields": {
                "consumption": data.consumption,
            },
        }
        for data in usage
    ]
    logger.info("Adding  Octopus usage information to influxdb")
    influxdb.write_points(influx_data)


def main() -> None:  # sourcery skip: extract-method
    """Query historical data and load into influxdb."""

    env = get_env()
    ago = 30
    days = 30
    measurements = [
        ("gas_consumption", "get_gas_consumption"),
        ("electricity_consumption", "get_electricity_consumption"),
        ("electricity_export", "get_electricity_export"),
    ]
    with InfluxConnection(database="octopus", reset=False).connect() as connection:
        with OctopusClient(apikey=env.get("octopus_apikey"), account=env.get("octopus_account")) as client:
            client.set_page_size(25000)
            client.set_group_by("day")
            for measurement, method in measurements:
                log_usage(
                    getattr(client, method)(ago=ago, days=days),
                    connection,
                    client.account_number,
                    measurement,
                )


if __name__ == "__main__":
    main()
