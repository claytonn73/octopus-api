"""Contains the Octopus API class and its methods."""

import logging
import json
from datetime import datetime, date, timedelta, timezone
from dataclasses import asdict # noqa F401

import dateutil.parser
import requests
from requests.auth import HTTPBasicAuth

from octopusapi.const import Octopus, Constants, Order, RegionID, Group, PriceType # noqa F401

import octopusapi.const

# Only export the Octopus Client
__all__ = ["OctopusClient"]


class OctopusError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class APIKeyError(OctopusError):
    def __init__(self, product):
        super().__init__("{} requires authorisation and no key provided.".format(product))


class OctopusClient():
    """Class for the Octopus API.

    Args:
        apikey (str): The apikey for the Octopus API
        account (str): The account number to be used for API requests
        postcode (str): The postcode to be used for API requests

    """

    def __init__(self, apikey: str = None, account: str = None, postcode: str = None) -> None:
        """Initialise the API client and get account information based on account number if provided.
        Args:
            apikey (str, optional): The apikey for the Octopus account. Defaults to None.
            account (str, optional): The account number for the Octopus account. Defaults to None.
            postcode (str, optional): The postcode that will be used for the API. Defaults to None
        """
        # Create a logger instance for messages from the API client
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialising Octopus API Client")
        self._session = requests.Session()
        self._api = Octopus
        # Octopus API uses the API key as user and accepts any value as the password
        self._user = apikey
        self._passwd = "anything"
        # Initialise dataclasses for the arguments and parms for the API
        self._api_args = octopusapi.const.apiargs()
        self._api_parms = octopusapi.const.apiparms()
        # If an account number if provided then check for an API key and then get details
        if account is not None:
            if self._user is not None:
                self._api_args.account = account
                self._get_account_information()
                # self_api_args.mpan = self._account_info.account.property.electricity_meter_point.mpan
                self._account_info.regionid = self._validate_mpan()
                self.logger.info(f'Grid Supply Region is {RegionID[self._account_info.regionid].value}')
            else:
                raise OctopusError("Account provided without API key.")
        # If no account number then check for a postcode and if provided set the regionid
        else:
            if postcode is not None:
                self._api_parms.postcode = postcode
                self._account_info.regionid = self._check_postcode()
                self.logger.info(f'Grid Supply Region is {RegionID[self._account_info.regionid].value}')

    def __enter__(self):
        """Entry function for the Octopus Client."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit function for the Octopus Client."""
        self._session.close()

    def close(self):
        """Close the requests session."""
        self._session.close()

    def _set_tariff_code(self, agreements: dict) -> None:
        """Iterate through the agreements passed and add the current agreement to the API arguments."""
        for agreement in agreements:
            if self._is_current(agreement):
                self.logger.info(f"tariff is: {agreement.tariff_code}")
                self._api_args.tariff_code = agreement.tariff_code
                self._api_args.product_code = agreement.tariff_code[5:-2]
                return
        self._api_args.tariff = None
        self._api_args.product = None

    def _get_account_information(self) -> None:
        """Populate information required for other API calls when provided an account ID and API key."""
        self._account_info = self._call_api(api_name="Account")
        # Get the information for the first property in the account only
        for property in self._account_info.properties:
            for meter_points in property.electricity_meter_points:
                if meter_points.is_export is True:
                    self._api_args.export_mpan = meter_points.mpan
                    self.logger.info(f"Export mpan found: {self._api_args.export_mpan}")
                    for agreement in meter_points.agreements:
                        if self._is_current(agreement):
                            self.logger.info(f"Current Export tariff is : {agreement.tariff_code}")
                elif meter_points.is_export is False:
                    self._api_args.mpan = meter_points.mpan
                    self.logger.info(f"Import mpan found: {self._api_args.mpan}")
                    for agreement in meter_points.agreements:
                        if self._is_current(agreement):
                            self.logger.info(f"Current Electricity tariff is : {agreement.tariff_code}")
            for meter_points in property.gas_meter_points:
                self._api_args.mprn = meter_points.mprn
                self.logger.info(f"Gas mprn found: {self._api_args.mprn}")
                for agreement in meter_points.agreements:
                    if self._is_current(agreement):
                        self.logger.info(f"Current Gas tariff is : {agreement.tariff_code}")

    def _validate_mpan(self) -> dict:
        """Query the provided meter point to get the grid supply point."""
        result = self._call_api(api_name="ElectricityMeterPoints")
        self.logger.debug(f'Grid supply point: {result.gsp}')
        return result.gsp

    def _check_postcode(self) -> str:
        """Return a group id for a particular postcode."""
        result = self._call_api(api_name="SupplyPoints")
        self.logger.info(f"Grid supply point: {result.results[0].group_id}")
        return result.results[0].group_id

    def test_api(self) -> None:
        """Run a series of API calls to test the API."""
        for api_name in self._api.apis:
            self.logger.info("Testing API endpoint: %s", api_name)
            self._api_args.product_code = self._api_args.import_product_code
            self._api_args.tariff_code = self._api_args.import_tariff_code
            # Get the enum for each endpoint
            # api_object = self._api.apis[api_name]
            # Call the api for the endpoint and log the response
            results = self._call_api(api_name=api_name)
            # self.logger.debug("Response: %s", results)
            # self.logger.debug("Resuts: %s", results)
            # Check that each section in the API response exists
            # self._parse_result(api_object.response, results, api_object.response)
            if api_name == "Products":
                self._api_args.product_code = results.results[0].code
                self._api_args.tariff_code = "E-1R-" + results.results[0].code + "-A"

    def set_period_from(self, start) -> None:
        """Set the from data for any queries using either a string or datetime object."""
        if isinstance(start, str):
            self._api_parms.period_from = datetime.strftime(dateutil.parser.parse(start), '%Y-%m-%dT%H:%MZ')
        elif isinstance(start, datetime):
            self._api_parms.period_from = datetime.strftime(start, '%Y-%m-%dT%H:%MZ')

    def set_period_to(self, end) -> None:
        """Set the to data for any queries using either a string or datetime object."""
        if isinstance(end, str):
            self._api_parms.period_to = datetime.strftime(dateutil.parser.parse(end), '%Y-%m-%dT%H:%MZ')
        elif isinstance(end, datetime):
            self._api_parms.period_to = datetime.strftime(end, '%Y-%m-%dT%H:%MZ')

    def set_active_at(self, active=datetime.now()) -> None:
        """Set the active at parameter for any queries using either a string or datetime object."""
        if isinstance(active, str):
            self._api_parms.tariffs_active_at = datetime.strftime(dateutil.parser.parse(active), '%Y-%m-%dT%H:%MZ')
        elif isinstance(active, datetime):
            self._api_parms.tariffs_active_at = datetime.strftime(active, '%Y-%m-%dT%H:%MZ')

    def set_page_size(self, size: int) -> None:
        """Set the page size for any queries."""
        self._api_parms.page_size = size

    def set_group_by(self, time: str) -> None:
        """Set the group by interval for any queries."""
        for grouping in octopusapi.const.Group:
            if time == grouping.value:
                self._api_parms.group_by = time

    @property
    def account_number(self) -> str:
        """The account number property."""
        return self._api_args.account

    def _set_startend(self, ago: int, days: int) -> None:
        """Sets the period_from and period_to arguments based on the input parameters

        Args:
            ago (int): number of days ago for the start of the period
            days (int): number of days ago for the end of the period
        """
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=days) - timedelta(minutes=5)
        self.set_period_from(start)
        self.set_period_to(end)

    def get_gas_consumption(self, intervals=48, ago: int = 7, days: int = 7) -> dict:
        """Get gas consumption information."""
        self._set_startend(ago, days)
        # self.set_page_size(intervals)
        response = {}
        for property in self._account_info.properties:
            for meter_point in property.gas_meter_points:
                for meter in meter_point.meters:
                    self._api_args.gas_serial_number = meter.serial_number
                    try:
                        results = self._call_api(api_name="GasConsumption")
                        # If we get any data back
                        if results.count > 0:
                            # If this is the first result then set the response equal to the results
                            if not response:
                                response = results
                            # Otherwise append the results to the results
                            else:
                                response.results += results.results
                                response.count += results.count
                    except requests.exceptions.HTTPError:
                        return None
                if response:
                    return response.results
                else:
                    return None

    def get_electricity_consumption_byrange(self, ago: int = 1, days: int = 1, daily: bool = True) -> dict:
        """Get electricity consumption information.
        Args:
            ago (int, optional): _description_. Defaults to 1.
            days (int, optional): _description_. Defaults to 1.
            daily (bool, optional): _description_. Defaults to True.

        Returns:
            dict: _description_
        """
        self._set_startend(ago, days)
        self._api_parms.group_by = None
        consumption = self.get_electricity_consumption(ago=ago, days=days)
        price_range = self.get_price_ranges()
        prices = self.get_import_prices()
        price_dict = {}
        usage = {}
        for price in prices:
            price_dict[price.valid_from] = price
        currentcost = iter(sorted(price_dict.keys()))
        coststart = next(currentcost)
        for entry in consumption:
            # Get the date in UTC
            if daily is True:
                date = entry.interval_start.astimezone(timezone.utc).strftime('%Y-%m-%dT00:00Z')
            else:
                date = entry.interval_start.astimezone(timezone.utc).strftime('%Y-%m-01T00:00Z')
            if usage.get(date) is None:
                usage.update({date: {}})
            # find the right price to start with
            while price_dict[coststart].valid_to <= entry.interval_start:
                coststart = next(currentcost)
            if price_dict[coststart].valid_to >= entry.interval_end:
                pricetype = price_range[price_dict[coststart].value_inc_vat].value
                usage[date][pricetype] = usage[date].setdefault(pricetype, 0) + entry.consumption
        return usage

    def get_electricity_consumption(self, intervals=48, ago: int = 7, days: int = 7) -> dict:
        """Get electricity consumption information."""
        self._set_startend(ago, days)
        # self.set_page_size(intervals)
        response = {}
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is False:
                    for meter in meter_point.meters:
                        self._api_args.electricity_serial_number = meter.serial_number
                        try:
                            results = self._call_api(api_name="ElectricityConsumption")
                            # If we get any data back
                            if results.count > 0:
                                # If this is the first result then set the response equal to the results
                                if not response:
                                    response = results
                                # Otherwise append the results to the results
                                else:
                                    response.results += results.results
                                    response.count += results.count
                        except requests.exceptions.HTTPError:
                            return None
                    if response:
                        return response.results
                    else:
                        return None

    def get_electricity_export(self, intervals=48, ago=7, days=7) -> dict:
        """Get electricity export information."""
        self._set_startend(ago, days)
        # self.set_page_size(intervals)
        response = {}
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is True:
                    for meter in meter_point.meters:
                        self._api_args.electricity_serial_number = meter.serial_number
                        try:
                            results = self._call_api(api_name="ElectricityExport")
                            # If we get any data back
                            if results.count > 0:
                                # If this is the first result then set the response equal to the results
                                if not response:
                                    response = results
                                # Otherwise append the results to the results
                                else:
                                    response.results += results.results
                                    response.count += results.count
                        except requests.exceptions.HTTPError:
                            return None
                    if response:
                        return response.results
                    else:
                        return None

    def calculate_electricity_cost(self, ago: int = 7) -> dict:
        """Calculate the total cost for electricity for a day."""
        self.get_import_product()
        self._set_startend(ago, 30)
        # Get the unit rates and store the value for each interval
        result = self._call_api(api_name="ElectricityStandardUnitRates")
        rates = {}
        for entry in result.results:
            rates[entry.valid_from] = entry.value_inc_vat
        # Get the consumption values and store the values for each interval
        self.get_import_product()
        result = self.get_electricity_consumption()
        consumption = {}
        for entry in result:
            consumption[entry.interval_start] = entry
        # Calculate the costs based on the rates and the consumption
        cost = {}
        currentcost = iter(sorted(rates.keys()))
        coststart = next(currentcost)
        for interval_start in sorted(consumption.keys()):
            # Iterate over the cost data until we find an interval that starts at the current time
            while interval_start <= coststart:
                coststart = next(currentcost)
            day = interval_start.date()
            # Then multiply the consumption by the rate to get the cost
            cost[day] = cost.setdefault(day, 0) + round(round(consumption[interval_start].consumption, 2)
                                                        * rates[coststart], 3)

        return cost

    def calculate_electricity_gain(self, ago: int = 7) -> dict:
        """Calculate the total cost for electricity for a day."""
        self.get_export_product()
        self._set_startend(ago, 30)
        # Get the unit rates and store the value for each interval
        result = self._call_api(api_name="ElectricityStandardUnitRates")
        rates = {}
        for entry in result.results:
            rates[entry.valid_from] = entry.value_inc_vat
        # Get the consumption values and store the values for each interval
        result = self.get_electricity_export()
        export = {}
        for entry in result:
            export[entry.interval_start] = entry
        # Calculate the costs based on the rates and the consumption
        gain = {}
        currentcost: list = iter(sorted(rates.keys()))
        coststart: float = next(currentcost)
        for interval_start in sorted(export.keys()):
            while interval_start <= coststart:
                coststart = next(currentcost)
            day: date = interval_start.date()
            gain[day] = gain.setdefault(day, 0) + round(round(export[interval_start].consumption, 2)
                                                        * rates[coststart], 3)
        return gain

    def get_import_product(self) -> dict:
        """Returns the details for the electricity import product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is False:
                    self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name="Product")
        for entry in octopusapi.const.RegionID:
            if entry.name == self._account_info.regionid:
                pass
            else:
                if entry.name in data.single_register_electricity_tariffs:
                    del data.single_register_electricity_tariffs[entry.name]
                if entry.name in data.dual_register_electricity_tariffs:
                    del data.dual_register_electricity_tariffs[entry.name]
                if entry.name in data.sample_quotes:
                    del data.sample_quotes[entry.name]
        return data

    def get_export_product(self) -> dict:
        """Returns the details for the electricity export product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is True:
                    self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name="Product")
        for entry in octopusapi.const.RegionID:
            if entry.name == self._account_info.regionid:
                pass
            else:
                if entry.name in data.single_register_electricity_tariffs:
                    del data.single_register_electricity_tariffs[entry.name]
                if entry.name in data.dual_register_electricity_tariffs:
                    del data.dual_register_electricity_tariffs[entry.name]
                if entry.name in data.sample_quotes:
                    del data.sample_quotes[entry.name]
        return data

    def get_gas_product(self) -> dict:
        """Returns the details for the gas product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.gas_meter_points:
                self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name="Product")
        for entry in octopusapi.const.RegionID:
            if entry.name == self._account_info.regionid:
                pass
            else:
                if entry.name in data.single_register_electricity_tariffs:
                    del data.single_register_electricity_tariffs[entry.name]
                if entry.name in data.dual_register_electricity_tariffs:
                    del data.dual_register_electricity_tariffs[entry.name]
                if entry.name in data.sample_quotes:
                    del data.sample_quotes[entry.name]
        return data

    def get_price_ranges(self) -> dict:
        """Return a dict of prices broken down into peak/offpeak and standard."""
        self.get_import_product()
        data = self._call_api(api_name="ElectricityStandardUnitRates")
        price_list = []
        price_dict = {}
        prev_date = datetime.now().date()
        for entry in data.results:
            current_date = entry.valid_from.date()
            # Collect the prices for each date
            if current_date == prev_date:
                if entry.value_inc_vat not in price_list:
                    if price_dict.get(entry.value_inc_vat) is None:
                        price_list.append(entry.value_inc_vat)
            # As we get to the next date evaluate the prices from the previous day
            else:
                price_list.sort()
                # Set the price labels depending on if we have 1, 2 or 3 prices per day
                if len(price_list) == 1:
                    price_dict[price_list[0]] = PriceType.STANDARD
                elif len(price_list) == 2:
                    price_dict[price_list[0]] = PriceType.OFFPEAK
                    price_dict[price_list[1]] = PriceType.PEAK
                elif len(price_list) == 3:
                    price_dict[price_list[0]] = PriceType.OFFPEAK
                    price_dict[price_list[1]] = PriceType.STANDARD
                    price_dict[price_list[2]] = PriceType.PEAK
                # Then reset the price list and start for the new date
                price_list = []
                if entry.value_inc_vat not in price_list:
                    if price_dict.get(entry.value_inc_vat) is None:
                        price_list.append(entry.value_inc_vat)
                prev_date = current_date
        return price_dict

    def get_import_prices(self) -> dict:
        """Return a list of the prices over time."""
        self.get_import_product()
        data = self._call_api(api_name="ElectricityStandardUnitRates")
        return data.results

    @property
    def electricity_standing_charge(self) -> float:
        """Get the current standing charge."""
        self.get_import_product()
        data = self._call_api(api_name="ElectricityStandingCharges")
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_export_price(self) -> float:
        """Get the current electricity export price."""
        self.get_export_product()
        data = self._call_api(api_name="ElectricityStandardUnitRates")
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_import_price(self) -> float:
        """Get the current electricity import price."""
        self.get_import_product()
        data = self._call_api(api_name="ElectricityStandardUnitRates")
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_gas_price(self) -> float:
        """Get the current gas price."""
        self.get_gas_product()
        data = octopusapi.const.rates(**self._call_api(api_name="GasStandardUnitRates"))
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def gas_standing_charge(self) -> float:
        """Get the current gas standing charge ."""
        self.get_gas_product()
        data = octopusapi.const.rates(**self._call_api(api_name="GasStandingCharges"))
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    def _call_api(self, api_name: str = "Products") -> dict:
        """Initialise the arguments required to call one of the REST APIs and then call it returning the results."""
        api_object = self._api.apis[api_name]
        # If the API request requires a key and we do not have one
        if (api_object.auth is True) & (self._user is None):
            raise APIKeyError(api_name)
        # Create a dictionary entry for the arguments required by the endpoint
        arguments = {}
        for entry in api_object.arguments:
            arguments.update({entry.value: getattr(self._api_args, entry.value)})
        # Create a parameter string including any parameters for the endpoint which have a defined value
        parm_string = ""
        for entry in api_object.parms:
            if getattr(self._api_parms, entry.value) is not None:
                if parm_string == "":
                    parm_string = f"?{entry.value}={getattr(self._api_parms, entry.value)}"
                else:
                    parm_string += f"&{entry.value}={getattr(self._api_parms, entry.value)}"
        # Create a URL from the supplied information
        url = "{}/{}/{}".format(self._api.url,
                                api_object.endpoint.format(**arguments),
                                parm_string)
        # Call the API endpoint and return the results
        # print(self._rest_request(url, api_object.auth))
        return api_object.response(**self._rest_request(url, api_object.auth))

    def _rest_request(self, url: str, auth: bool = False) -> dict:
        """Use the requests module to call the REST API and check the response."""
        # Only pass the API key if it is required
        if auth is True:
            if self._user is None:
                raise APIKeyError(url)
            else:
                authorisation = HTTPBasicAuth(self._user, self._passwd)
        else:
            authorisation = None
        # Initialize an empty dict for the response
        response = {}
        # Iterate while we have a valid url in order to handle the requirement for multiple queries
        while url is not None:
            try:
                self.logger.info("Calling Octopus API: %s", url)
                results = self._session.get(url=url, auth=authorisation, timeout=60)
                self.logger.debug(f'Response received: {results}')
                results.raise_for_status()
                # Check the REST API response status
                if results.status_code != requests.codes.ok:
                    self.logger.error("API Error encountered for URL: %s Status Code: %s", url, results.status_code)
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)
            except requests.exceptions.RequestException as err:
                raise SystemExit(err)
            self.logger.debug("Formatted API results:\n %s", json.dumps(results.json(), indent=2))
            # If this is the first result then return the json data
            if not response:
                response = results.json()
            # Otherwise we are adding to an existing dict and we should concatenate the results
            else:
                response["results"] += results.json()["results"]
                response["count"] += results.json()["count"]
            # If we are told this is not the last response in a list then we need to iterate
            if "next" in results.json():
                url = results.json()["next"]
            # Otherwise end the iteration
            else:
                break
        return response

    def _is_current(self, entry: dict) -> bool:
        """Determine if an entry is current based on the valid_from and valid_to fields."""
        result = True
        if getattr(entry, Constants.VALID_FROM.value) is not None:
            from_date = getattr(entry, Constants.VALID_FROM.value)
            if from_date > datetime.now(from_date.tzinfo):
                result = False
        if getattr(entry, Constants.VALID_TO.value) is not None:
            to_date = getattr(entry, Constants.VALID_TO.value)
            if to_date < datetime.now(from_date.tzinfo):
                result = False
        self.logger.debug(f'From date: {getattr(entry, Constants.VALID_FROM.value)} '
                          f'To date: {getattr(entry, Constants.VALID_TO.value)} Result: {result}')
        return result

    def _is_between(self, entry: dict, time: datetime) -> bool:
        """Determine if an entry is the correct one based on the valid_from and valid_to fields."""
        result = True
        if entry[Constants.VALID_FROM.value] is not None:
            from_date = dateutil.parser.parse(entry[entry.valid_from.name])
            if from_date > time:
                result = False
        if entry[Constants.VALID_TO.value] is not None:
            to_date = dateutil.parser.parse(entry[Constants.VALID_TO.value])
            if to_date < time:
                result = False
        self.logger.debug(f'From date: {entry[Constants.VALID_FROM.value]} '
                          f'To date: {entry[Constants.VALID_TO.value]} Time: {time} Result: {result}')
        return result
