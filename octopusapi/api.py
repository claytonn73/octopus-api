"""Contains the Octopus API class and its methods."""

import logging
import json
from datetime import datetime, date, timedelta

import dateutil.parser
import requests
from requests.auth import HTTPBasicAuth

from octopusapi.const import Octopus

# Only export the Octopus Client
__all__ = ["OctopusClient"]


class OctopusError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class APIKeyError(OctopusError):
    def __init__(self, product):
        super().__init__("{} requires authorisation and no key provided.".format(product))


class OctopusClient:
    """Class for the Octopus API.

    Args:
        apikey (str): The apikey for the Octopus API
        account (str): The account number to be used for API requests
        postcode (str): The postcode to be used for API requests

    """

    def __init__(self, apikey=None, account=None, postcode=None):
        """Initialise the API client and get account information based on account number if provided."""
        # Create a logger instance for messages from the API client
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialising Octopus API Client")
        self._session = requests.Session()
        self._apikey = apikey
        self._api_args = {}
        self._api_parms = {}
        # Set default ordering of response to be ascending order of date
        self._api_parms.update({"order_by": "period"})
        self._group_id = None
        self._account_info = {}
        if account is not None:
            if self._apikey is not None:
                self._api_args.update({"account": account})
                self._get_account_information()
                self._group_id = self._validate_mpan()["gsp"]
            else:
                raise OctopusError("Account provided without API key.")
        else:
            if postcode is not None:
                self._api_parms.update({"postcode": postcode})
                self._group_id = self._check_postcode()[0]["group_id"]

    def __enter__(self):
        """Entry function for the Octopus Client."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit function for the Octopus Client."""
        self._session.close()

    def close(self):
        """Close the requests session."""
        self._session.close()

    def _set_tariff_code(self, tariff, product, agreements):
        """Set api arguments for an agreement."""
        for agreement in agreements:
            if agreement["valid_to"] is not None:
                valid_date = dateutil.parser.parse(agreement["valid_to"])
                if valid_date > datetime.now(valid_date.tzinfo):
                    self.logger.debug("%s tariff is: %s", product, agreement["tariff_code"])
                    self._api_args.update({tariff: agreement["tariff_code"]})
                    self._api_args.update({product: agreement["tariff_code"][5:-2]})
            else:
                self.logger.debug("%s tariff is: %s", product, agreement["tariff_code"])
                self._api_args.update({tariff: agreement["tariff_code"]})
                self._api_args.update({product: agreement["tariff_code"][5:-2]})

    def debug_account_information(self):
        """Populate information required for other API calls when provided an account ID and API key."""
        try:
            results = self._call_api(api_name="Account")
        except requests.exceptions.HTTPError:
            return None
        print(results.json())
        print(results.json()["properties"][0]["electricity_meter_points"][0])
        print("done")
        for meter_points in results.json()["properties"][0]["electricity_meter_points"]:
            for mpan in meter_points['meters']:
                self._api_args.update({"electricity_serial_number":
                                       mpan['serial_number']})
                print(self.get_electricity_consumption())
        return results.json()

    def _get_account_information(self):
        """Populate information required for other API calls when provided an account ID and API key."""
        try:
            results = self._call_api(api_name="Account")
        except requests.exceptions.HTTPError:
            return None
        for metre_points in results.json()["properties"][0]["electricity_meter_points"]:
            if metre_points["is_export"] is True:
                self._api_args.update({"export_mpan": metre_points["mpan"]})
                self._set_tariff_code("export_tariff_code", "export_product_code", metre_points["agreements"])
                self._account_info.update(
                    {"electricity_export": metre_points["consumption_standard"]})
                self.logger.debug("Export mpan found: %s", self._api_args["export_mpan"])
                self._api_args.update({"electricity_export_serial_number":
                                       metre_points["meters"][0]["serial_number"]})
                self._api_args.update({"electricity_export_serial_numbers": metre_points["meters"]})
            if metre_points["is_export"] is False:
                if metre_points['profile_class'] == 2:
                    self._account_info.update(
                        {"electricity_consumption": metre_points["consumption_day"] + metre_points["consumption_night"]})
                else:
                    self._account_info.update(
                        {"electricity_consumption": metre_points["consumption_standard"]})
                self._api_args.update({"mpan": metre_points["mpan"]})
                self._api_args.update({"electricity_serial_number": metre_points["meters"][0]["serial_number"]})
                self._api_args.update({"electricity_serial_numbers": metre_points["meters"]})
                self._set_tariff_code("import_tariff_code", "import_product_code", metre_points["agreements"])
                self.logger.debug("Import mpan found: %s", self._api_args["mpan"])
        for metre_points in results.json()["properties"][0]["gas_meter_points"]:
            self._account_info.update({"gas_consumption": metre_points["consumption_standard"]})
            self._api_args.update({"mprn": metre_points["mprn"]})
            self._api_args.update({"gas_serial_number": metre_points["meters"][0]["serial_number"]})
            self._api_args.update({"gas_serial_numbers": metre_points["meters"]})
            self._set_tariff_code("gas_tariff_code", "gas_product_code", metre_points["agreements"])
            self.logger.debug("Gas mprn found: %s", self._api_args["mprn"])
        return results.json()

    def _validate_mpan(self):
        """Query the provided meter point to get the grid supply point."""
        try:
            results = self._call_api(api_name="ElectricityMeterPoints")
            self.logger.debug("Grid supply point: %s", results.json()["gsp"])
            return results.json()
        except requests.exceptions.HTTPError:
            return None

    def _check_postcode(self):
        """Return a group id for a particular postcode."""
        try:
            result = self._call_api(api_name="SupplyPoints")
            self.logger.debug("Grid supply point: %s", result.json()["results"][0]["group_id"])
            return result.json()["results"][0]["group_id"]
        except requests.exceptions.HTTPError:
            return None

    def _parse_result(self, api_object, result, description):
        for section in description:
            if section == "group_id":
                for key in result.keys():
                    self.logger.info("Found group_id: %s %s %s", result, key, result[key])
                    # self._parse_result(api_object, result[key], api_object[section].value)
            if section in result:
                if result[section] is not None:
                    if description[section] is int:
                        self.logger.info("Found: %s %s %s", section, description[section],
                                         isinstance(result[section], description[section]))
                    if description[section] is float:
                        self.logger.info("Found:  %s %s %s", section, description[section],
                                         isinstance(result[section], description[section]))
                    if description[section] is str:
                        self.logger.info("Found: %s %s %s", section, description[section],
                                         isinstance(result[section], description[section]))
                    if description[section] is datetime:
                        test_date = dateutil.parser.parse(result[section])
                        self.logger.info(section, description[section], isinstance(
                            test_date, description[section]))
                    if description[section] == "url":
                        # valid = validators.url(result[section])
                        self.logger.info("url")
                    if description[section] is list:
                        self._parse_result(api_object, result[section][0], api_object[section].value)
                    if description[section] is dict:
                        self.logger.info(section)
                        self.logger.info(result[section])
                        self._parse_result(api_object, result[section], api_object[section].value)
            else:
                self.logger.info("Not found: %s", section)

    def test_api(self):
        """Run a series of API calls to test the API."""
        for api_name in Octopus.API_LIST.value:
            self.logger.info("Testing API endpoint: %s", api_name)
            # Get the enum for each endpoint
            api_object = Octopus.API_LIST.value[api_name]
            try:
                # Call the api for the endpoint and log the response
                results = self._call_api(api_name=api_name)
                self.logger.info("Response: %s", results)
                self.logger.info("Resuts: %s", results.json())
                # Check that each section in the API response exists
                self._parse_result(api_object, results.json(), api_object.RESPONSE.value)
            except requests.exceptions.HTTPError:
                self.logger.error("Error for endpoint: %s", api_name)
            if api_name == "Products":
                self._api_args.update({"product_code": results.json()["results"][0]["code"]})
                # self._api_args.update({"tariff_code": "E-1R-" + results.json()["results"][0]["code"] + "-A"})
            if api_name == "Product":
                self._api_args.update({"product_code": self._api_args["import_product_code"]})
                self._api_args.update({"tariff_code": self._api_args["import_tariff_code"]})

    def set_period_from(self, start):
        """Set the from data for any queries using either a string or datetime object."""
        if isinstance(start, str):
            valid_date = dateutil.parser.parse(start)
            self._api_parms.update(
                {"period_from": datetime.strftime(valid_date, '%Y-%m-%dT%H:%MZ')})
        if isinstance(start, datetime):
            self._api_parms.update({"period_from": datetime.strftime(start, '%Y-%m-%dT%H:%MZ')})

    def set_period_to(self, end):
        """Set the to data for any queries using either a string or datetime object."""
        if isinstance(end, str):
            valid_date = dateutil.parser.parse(end)
            self._api_parms.update({"period_to": datetime.strftime(valid_date, '%Y-%m-%dT%H:%MZ')})
        if isinstance(end, datetime):
            self._api_parms.update({"period_to": datetime.strftime(end, '%Y-%m-%dT%H:%MZ')})

    def set_active_at(self, active=None):
        """Set the active at parameter for any queries using either a string or datetime object."""
        if active is None:
            valid_date = datetime.now()
        else:
            if isinstance(active, str):
                valid_date = dateutil.parser.parse(active)
                self._api_parms.update({"tariffs_active_at": datetime.strftime(valid_date, '%Y-%m-%dT%H:%MZ')})
            if isinstance(active, datetime):
                self._api_parms.update({"tariffs_active_at": datetime.strftime(active, '%Y-%m-%dT%H:%MZ')})

    def set_page_size(self, size):
        """Set the page size for any queries."""
        self._api_parms.update({"page_size": size})

    def set_group_by(self, time):
        """Set the group by interval for any queries."""
        if time in ["hour", "day", "week", "month", "quarter"]:
            self._api_parms.update({"group_by": time})

    def get_account_number(self):
        """Get the account number."""
        return self._api_args["account"]

    def get_gas_consumption(self, intervals=48, ago=7, days=7):
        """Get gas consumption information."""
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=days) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)
        self.set_page_size(intervals)
        for meters in self._api_args["gas_serial_numbers"]:
            self._api_args.update({"gas_serial_number": meters['serial_number']})
            try:
                results = self._call_api(api_name="GasConsumption")
                # self.logger.debug("Gas consumption json: {}".format(results.json()))
                if results.json()['count'] > 0:
                    return results.json()["results"]
            except requests.exceptions.HTTPError:
                return None

    def get_electricity_consumption(self, intervals=48, ago=7, days=7):
        """Get electricity consumption information."""
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=days) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)
        self.set_page_size(intervals)
        for meters in self._api_args["electricity_serial_numbers"]:
            self._api_args.update({"electricity_serial_number": meters['serial_number']})
            try:
                results = self._call_api(api_name="ElectricityConsumption")
                self.logger.debug("Electricity consumption json: {}".format(results.json()))
                if results.json()['count'] > 0:
                    return results.json()["results"]
            except requests.exceptions.HTTPError:
                return None

    def get_electricity_export(self, intervals=48, ago=7, days=7):
        """Get electricity consumption information."""
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=days) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)
        self.set_page_size(intervals)
        for meters in self._api_args["electricity_export_serial_numbers"]:
            self._api_args.update({"electricity_export_serial_number": meters['serial_number']})
            try:
                results = self._call_api(api_name="ElectricityExport")
                # self.logger.debug("Gas consumption json: {}".format(results.json()))
                if results.json()['count'] > 0:
                    return results.json()["results"]
            except requests.exceptions.HTTPError:
                return None

    def calculate_electricity_cost(self, ago):
        """Calculate the total cost for electricity for a day."""
        self._api_args.update({"product_code": self._api_args["import_product_code"]})
        self._api_args.update({"tariff_code": self._api_args["import_tariff_code"]})
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=30) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)
        # Get the unit rates and store the value for each interval
        rates = {}
        result = self._call_api(api_name="ElectricityStandardUnitRates")
        for entry in result.json()["results"]:
            rates[dateutil.parser.parse(entry["valid_from"])] = entry
        # Get the consumption values and store the values for each interval
        result = self._call_api(api_name="ElectricityConsumption")
        consumption = {}
        for entry in result.json()["results"]:
            consumption[dateutil.parser.parse(entry["interval_start"])] = entry
        # Calculate the costs based on the rates and the consumption
        cost = {}
        currentcost = iter(sorted(rates.keys()))
        coststart = next(currentcost)
        for interval_start in sorted(consumption.keys()):
            # Iterate over the cost data until we find an interval that starts at the current time
            while interval_start <= dateutil.parser.parse(rates[coststart]["valid_from"]):
                coststart = next(currentcost)
            day = interval_start.date()
            # Then multiply the consumption by the rate to get the cost
            if day in cost:
                cost[day] = cost[day] + round(round(consumption[interval_start]["consumption"], 2) * rates[coststart]["value_inc_vat"], 3)
            else:
                cost[day] = round(round(consumption[interval_start]["consumption"], 2) * rates[coststart]["value_inc_vat"], 3)

        return cost

    def calculate_electricity_gain(self, ago):
        """Calculate the total cost for electricity for a day."""
        self._api_args.update({"product_code": self._api_args["export_product_code"]})
        self._api_args.update({"tariff_code": self._api_args["export_tariff_code"]})
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=30) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)
        # Get the unit rates and store the value for each interval
        rates = {}
        result = self._call_api(api_name="ElectricityStandardUnitRates")
        for entry in result.json()["results"]:
            rates[dateutil.parser.parse(entry["valid_from"])] = entry
        # Get the consumption values and store the values for each interval
        result = self._call_api(api_name="ElectricityExport")
        export = {}
        for entry in result.json()["results"]:
            export[dateutil.parser.parse(entry["interval_start"])] = entry
        # Calculate the costs based on the rates and the consumption
        gain = {}
        currentcost = iter(sorted(rates.keys()))
        coststart = next(currentcost)
        for interval_start in sorted(export.keys()):
            while interval_start <= dateutil.parser.parse(rates[coststart]["valid_from"]):
                coststart = next(currentcost)
            day = interval_start.date()
            if day in gain:
                gain[day] = gain[day] + round(round(export[interval_start]["consumption"], 2) * rates[coststart]["value_inc_vat"], 3)
            else:
                gain[day] = round(round(export[interval_start]["consumption"], 2) * rates[coststart]["value_inc_vat"], 3)
        return gain

    def get_standing_charge(self):
        """Get the standing charge ."""
        self._api_args.update({"product_code": self._api_args["import_product_code"]})
        self._api_args.update({"tariff_code": self._api_args["import_tariff_code"]})
        try:
            results = self._call_api(api_name="ElectricityStandingCharges")
            for entry in results.json()["results"]:
                from_date = dateutil.parser.parse(entry["valid_from"])
                if entry["valid_to"] is None:
                    to_date = datetime.now(from_date.tzinfo) + timedelta(minutes=5)
                else:
                    to_date = dateutil.parser.parse(entry["valid_to"])
                if from_date < datetime.now(from_date.tzinfo):
                    if to_date > datetime.now(to_date.tzinfo):
                        return entry["value_inc_vat"]
        except requests.exceptions.HTTPError:
            return None

    def get_current_electricity_price(self, direction):
        """Get the current electricity price either import or export."""
        if direction == "export":
            self._api_args.update({"product_code": self._api_args["export_product_code"]})
            self._api_args.update({"tariff_code": self._api_args["export_tariff_code"]})
        if direction == "import":
            self._api_args.update({"product_code": self._api_args["import_product_code"]})
            self._api_args.update({"tariff_code": self._api_args["import_tariff_code"]})
        try:
            results = self._call_api(api_name="ElectricityStandardUnitRates")
            for entry in results.json()["results"]:
                from_date = dateutil.parser.parse(entry["valid_from"])
                to_date = dateutil.parser.parse(entry["valid_to"])
                if from_date < datetime.now(from_date.tzinfo):
                    if to_date > datetime.now(to_date.tzinfo):
                        return entry["value_inc_vat"]
        except requests.exceptions.HTTPError:
            return None

    def get_current_gas_price(self):
        """Get the current gas price."""
        try:
            results = self._call_api(api_name="GasStandardUnitRates")
            for entry in results.json()["results"]:
                if entry["valid_from"] is None:
                    return entry["value_inc_vat"]
                else:
                    from_date = dateutil.parser.parse(entry["valid_from"])
                    to_date = dateutil.parser.parse(entry["valid_to"])
                    if from_date < datetime.now(from_date.tzinfo):
                        if to_date > datetime.now(to_date.tzinfo):
                            return entry["value_inc_vat"]
            return None
        except requests.exceptions.HTTPError:
            return None

    def print_api_response(self, api="Products"):
        """Prints the raw response from the API."""
        try:
            results = self._call_api(api_name=api)
            print(json.dumps(results.json(), indent=4))
            return None
        except requests.exceptions.HTTPError:
            return None

    def _call_api(self, api_name="Products"):
        """Initialise the arguments required to call one of the REST APIs and then call it returning the results."""
        parm_string = ""
        arguments = {}
        api_object = Octopus.API_LIST.value[api_name]
        # If the API request requires a key and we do not have one
        if (api_object.AUTH.value is True) & (self._apikey is None):
            raise APIKeyError(api_name)
        # Create a dictionary entry for the arguments required by the endpoint
        for entry in api_object.ARGUMENTS.value:
            arguments.update({entry: self._api_args[entry]})
        # Create a parameter string including any parameters for the endpoint which have a defined value
        for entry in api_object.PARMS.value:
            if entry in self._api_parms:
                if parm_string == "":
                    parm_string = f"?{entry}={self._api_parms[entry]}"
                else:
                    parm_string = parm_string + f"&{entry}={self._api_parms[entry]}"
        # Create a URL from the supplied information
        url = "{}/{}/{}".format(Octopus.URL.value,
                                api_object.ENDPOINT.value.format(**arguments),
                                parm_string)
        self.logger.debug("URL for API call: %s", url)
        # Call the API endpoint and return the results
        return self._rest_request(url, api_object.AUTH.value)

    def _rest_request(self, url, auth=False):
        """Use the requests module to call the REST API and check the response."""
        # Only pass the API key if it is required
        authorisation = None
        if auth is True:
            if self._apikey is None:
                raise APIKeyError(url)
            else:
                authorisation = HTTPBasicAuth(self._apikey, "anything")
        try:
            results = self._session.get(url=url, auth=authorisation, timeout=60)
            results.raise_for_status()
            # Check the REST API response status
            if results.status_code != requests.codes.ok:
                self.logger.error("API Error encountered for URL: %s Status Code: %s", url, results.status_code)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        except requests.exceptions.RequestException as err:
            raise SystemExit(err)
        return results
