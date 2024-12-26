"""Contains the Octopus API class and its methods."""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Callable

import dateutil.parser
import requests
import ujson
from requests.auth import HTTPBasicAuth

import octopusapi.const
from octopusapi.const import APIConstants, APIList, Octopus, PriceType

# Only export the Octopus Client
__all__ = ["OctopusClient"]


class OctopusError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class APIKeyError(OctopusError):
    def __init__(self, product):
        super().__init__(f"{product} requires authorisation and no key provided.")


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
        # If an account number if provided then check for an API key and then get details
        if account is not None and apikey is None:
            raise OctopusError("Account provided without API key.")            
        if self._user:
            self._api.arguments.account = account
            self._get_account_information()
            self._account_info.regionid = self._validate_mpan()
            self.logger.info(f'Grid Supply Region is {self._account_info.regionid.value}')               
        # If no account number then check for a postcode and if provided set the regionid
        elif postcode:
            self._api.parameters.postcode = postcode
            self._account_info.regionid = self._check_postcode()
            self.logger.info(f'Grid Supply Region is {self._account_info.regionid.value}')

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
                self._api.arguments.tariff_code = agreement.tariff_code
                self._api.arguments.product_code = agreement.tariff_code[5:-2]

    def _parse_gas_meterpoint(self, meter_point) -> None:
        self._api.arguments.mprn = meter_point.mprn
        self.logger.info(f"Gas mprn found: {self._api.arguments.mprn}")
        for agreement in meter_point.agreements:
            if self._is_current(agreement):
                self.logger.info(f"Current Gas tariff is : {agreement.tariff_code}")
                self._account_info.gas_tariff = agreement.tariff_code             
                
    def _parse_electricity_meterpoint(self, meter_point) -> None:
        if meter_point.is_export:
            self._api.arguments.export_mpan = meter_point.mpan
            self.logger.info(f"Export mpan found: {self._api.arguments.export_mpan}")
            for agreement in meter_point.agreements:
                if self._is_current(agreement):
                    self.logger.info(f"Current Export tariff is : {agreement.tariff_code}")
                    self._account_info.export_tariff = agreement.tariff_code
        else:
            self._api.arguments.mpan = meter_point.mpan
            self.logger.info(f"Import mpan found: {self._api.arguments.mpan}")
            for agreement in meter_point.agreements:
                if self._is_current(agreement):
                    self.logger.info(f"Current Electricity tariff is : {agreement.tariff_code}")
                    self._account_info.import_tariff = agreement.tariff_code                         
                            
    def _get_account_information(self) -> None:
        """Populate information required for other API calls when provided an account ID and API key."""
        self._account_info = self._call_api(api_name=APIList.Account)
        # Get the information for the first property in the account only
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                self._parse_electricity_meterpoint(meter_point)                
            for meter_point in property.gas_meter_points:
                self._parse_gas_meterpoint(meter_point)

    def _validate_mpan(self) -> octopusapi.const.RegionID:
        """Query the provided meter point to get the grid supply point."""
        result = self._call_api(api_name=APIList.ElectricityMeterPoints)
        self.logger.debug(f'Grid supply point: {result.gsp.value}')
        return result.gsp

    def _check_postcode(self) -> octopusapi.const.RegionID:
        """Return a group id for a particular postcode."""
        result = self._call_api(api_name=APIList.SupplyPoints)
        self.logger.info(f"Grid supply point: {result.results[0].group_id}")
        return result.results[0].group_id

    def set_period_from(self, start: str | datetime) -> None:
        """Set the from data for any queries using either a string or datetime object."""
        if isinstance(start, str):
            start = dateutil.parser.parse(start)
        self._api.parameters.period_from = datetime.strftime(start, '%Y-%m-%dT%H:%MZ')

    def set_period_to(self, end: str | datetime) -> None:
        """Set the to data for any queries using either a string or datetime object."""
        if isinstance(end, str):
            end = dateutil.parser.parse(end)
        self._api.parameters.period_to = datetime.strftime(end, '%Y-%m-%dT%H:%MZ')

    def set_active_at(self, active: str | datetime = datetime.now()) -> None:
        """Set the active at parameter for any queries using either a string or datetime object."""
        if isinstance(active, str):
            active = dateutil.parser.parse(active)
        self._api.parameters.tariffs_active_at = datetime.strftime(active, '%Y-%m-%dT%H:%MZ')

    def set_page_size(self, size: int) -> None:
        """Set the page size for any queries."""
        self._api.parameters.page_size = size

    def set_group_by(self, time: str) -> None:
        """Set the group by interval for any queries."""
        for grouping in octopusapi.const.Group:
            if time == grouping.value:
                self._api.parameters.group_by = time

    @property
    def account_number(self) -> str:
        """The account number property."""
        return self._api.arguments.account

    def _set_startend(self, ago: int, days: int) -> None:
        """Sets the period_from and period_to arguments based on the input parameters

        Args:
            ago (int): number of days ago for the start of the period
            days (int): number of days ago for the end of the period
        """
        start = datetime.combine(date.today() - timedelta(days=ago), datetime.min.time())
        end = start + timedelta(days=days) - timedelta(minutes=5)
        # print("setting", start,end)
        self.set_period_from(start)
        self.set_period_to(end)

    def get_gas_consumption(self, ago: int = 7, days: int = 7) -> dict:
        """Get gas consumption information."""
        self._set_startend(ago, days)
        response = {'results': [], 'count': 0}
        meters = (meter for property in self._account_info.properties
                    for meter_point in property.gas_meter_points
                    for meter in meter_point.meters)        
        for meter in meters:                    
            self._api.arguments.gas_serial_number = meter.serial_number
            results = self._call_api(api_name=APIList.GasConsumption)
            if results.count > 0:
                response['results'] += results.results
                response['count'] += results.count
        return response['results']

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
        self._api.parameters.group_by = None
        consumption = self.get_electricity_consumption(ago=ago, days=days)
        price_range = self.price_ranges
        price_dict = {price.valid_from: price for price in self.import_prices}        
        currentcost = iter(sorted(price_dict.keys()))
        coststart = next(currentcost)
        usage = defaultdict(dict)        
        for entry in consumption:
            if daily:
                date = entry.interval_start.replace(hour=0, minute=0, second=0, microsecond=0) 
            else:
                date = entry.interval_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0) 
            # find the right price to start with
            while price_dict[coststart].valid_to <= entry.interval_start:
                coststart = next(currentcost)
            if price_dict[coststart].valid_to >= entry.interval_end:
                pricetype = price_range[price_dict[coststart].value_inc_vat].value
                usage[date][pricetype] = round(usage[date].setdefault(pricetype, 0) + entry.consumption, 2)
        return usage

    def get_electricity_consumption(self, ago: int = 7, days: int = 7) -> dict:
        """Get electricity consumption information."""
        self._set_startend(ago, days)
        response = {'results': [], 'count': 0}
        meters = (meter for property in self._account_info.properties
            for meter_point in property.electricity_meter_points
            for meter in meter_point.meters if not meter_point.is_export)  
        for meter in meters:
            self._api.arguments.electricity_serial_number = meter.serial_number
            results = self._call_api(api_name=APIList.ElectricityConsumption)
            if results.count > 0:
                response['results'] += results.results
                response['count'] += results.count
        return response['results'] 


    def get_electricity_export(self, ago: int = 7, days: int = 7) -> dict | None:
        """Get electricity export information."""
        self._set_startend(ago, days)
        response = {'results': [], 'count': 0}
        meters = (meter for property in self._account_info.properties
            for meter_point in property.electricity_meter_points
            for meter in meter_point.meters if meter_point.is_export)  
        for meter in meters:        
            self._api.arguments.export_serial_number = meter.serial_number
            results = self._call_api(api_name=APIList.ElectricityExport)
            if results.count > 0:
                response['results'] += results.results
                response['count'] += results.count
        return response['results']


    def get_standard_unit_rates(self) -> octopusapi.const.rates:
        return self._call_api(api_name=APIList.ElectricityStandardUnitRates).results
    
    def get_gas_standard_unit_rates(self) -> octopusapi.const.rates:
        return self._call_api(api_name=APIList.GasStandardUnitRates).results
        
    def get_electricity_prices(self, ago: int = 7) -> octopusapi.const.rates:
        """Calculate the total cost for electricity for a day."""
        self.import_product
        self._set_startend(ago, ago)
        # Get the unit rates and store the value for each interval
        return self.get_standard_unit_rates()

    def _calculate_price(self, rates, amount) -> dict: 
        price = {}
        cost_iterator = iter(sorted(rates.keys()))
        coststart = next(cost_iterator)
        current_cost = coststart        
        for interval_start in sorted(amount.keys()):
            # Iterate over the cost data until we find an interval that starts after the current time        
            # use the prior interval for the cost
            while interval_start >= coststart:
                current_cost = coststart
                try:
                    coststart = next(cost_iterator)
                except StopIteration:
                    break
            day = interval_start.date()
            # Then multiply the consumption by the rate to get the cost
            price[day] = price.setdefault(day, 0) + round(round(amount[interval_start].consumption, 2)
                                                        * rates[current_cost], 3)
            # print(interval_start, amount[interval_start].consumption, rates[current_cost] )
        return price

    def calculate_electricity_cost(self, ago: int = 7) -> dict:
        """Calculate the total cost for electricity for a day."""
        self.import_product
        self._set_startend(ago, ago)
        # Get the unit rates and store the value for each interval
        rates = {entry.valid_from: entry.value_inc_vat for entry in self.get_standard_unit_rates()}
        # Get the consumption values and store the values for each interval
        consumption = {entry.interval_start: entry for entry in self.get_electricity_consumption(ago, ago)}   
        return self._calculate_price(rates,consumption)

    def calculate_electricity_gain(self, ago: int = 7) -> dict:
        """Calculate the total cost for electricity for a day."""
        self.export_product
        self._set_startend(ago, ago)
        # Get the unit rates and store the value for each interval
        rates = {entry.valid_from: entry.value_inc_vat for entry in self.get_standard_unit_rates()}
        # Get the consumption values and store the values for each interval
        export = {entry.interval_start: entry for entry in self.get_electricity_export(ago, ago)}
        # Calculate the costs based on the rates and the consumption
        return self._calculate_price(rates,export)        

    def _delete_redundant(self, data: octopusapi.const.product) -> octopusapi.const.product:
        """Deletes entries in the product API data that is not relevant to the region ID
        for the current account.
        """
        delete_items = ["single_register_electricity_tariffs",
                        "dual_register_electricity_tariffs",
                        "single_register_gas_tariffs",
                        "sample_quotes"]
        for item in delete_items:
            if getattr(data, item) != {}:
                for entry in octopusapi.const.RegionID:
                    if entry != self._account_info.regionid:
                        del getattr(data, item)[entry]
        return data
        

    @property
    def import_product(self) -> octopusapi.const.product:
        """Returns the details for the electricity import product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is False:
                    self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name=APIList.Product)
        return self._delete_redundant(data)


    @property
    def export_product(self) -> octopusapi.const.product:
        """Returns the details for the electricity export product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.electricity_meter_points:
                if meter_point.is_export is True:
                    self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name=APIList.Product)
        # Delete redundant region information
        return self._delete_redundant(data)

    @property
    def gas_product(self) -> octopusapi.const.product:
        """Returns the details for the gas product for the account
        deleting the regions that are not relevant for the account
        """
        for property in self._account_info.properties:
            for meter_point in property.gas_meter_points:
                self._set_tariff_code(meter_point.agreements)
        data = self._call_api(api_name=APIList.Product)
        # Delete redundant region information
        return self._delete_redundant(data)

    @property
    def price_ranges(self) -> dict:
        """Return a dict of prices broken down into peak/offpeak and standard."""
        self.import_product
        data = self.get_standard_unit_rates()
        price_list = []
        price_dict = {}
        prev_date = datetime.now().date()
        for entry in data:
            current_date = entry.valid_from.date()
            # Collect the prices for each date
            if (current_date == prev_date) and (entry.value_inc_vat not in price_list):
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
                if (entry.value_inc_vat not in price_list) and (price_dict.get(entry.value_inc_vat) is None):
                        price_list.append(entry.value_inc_vat)
                prev_date = current_date
        return price_dict

    @property
    def region_name(self) -> str:
        """Return the name of the region."""
        return self._account_info.regionid.value
    
    @property
    def import_prices(self) -> octopusapi.const.rate:
        """Return a list of the prices over time."""
        self.import_product
        return self.get_standard_unit_rates()

    @property
    def electricity_standing_charge(self) -> float | None:
        """Get the current standing charge."""
        self.import_product
        data = self._call_api(api_name=APIList.ElectricityStandingCharges)
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_export_price(self) -> float | None:
        """Get the current electricity export price."""
        self.export_product
        for entry in self.get_standard_unit_rates():
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_import_price(self) -> float | None:
        """Get the current electricity import price."""
        self.import_product
        for entry in self.get_standard_unit_rates():
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def current_gas_price(self) -> float | None:
        """Get the current gas price."""
        self.gas_product
        for entry in self.get_gas_standard_unit_rates():
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    @property
    def gas_standing_charge(self) -> float | None:
        """Get the current gas standing charge ."""
        self.gas_product
        data = self._call_api(api_name=APIList.GasStandingCharges)
        for entry in data.results:
            if self._is_current(entry) is True:
                return entry.value_inc_vat
        return None

    def _call_api(self, api_name: octopusapi.const.Endpoint = APIList.Products) -> Callable:
        """Initialise the arguments required to call one of the REST APIs and then call it returning the results."""
        self.logger.info("Calling Octopus API: %s", api_name.name)        
        # If the API request requires a key and we do not have one
        if (api_name.value.auth is True) and (self._user is None):
            raise APIKeyError(api_name)
        # Create a dictionary entry for the arguments required by the endpoint
        arguments = {
            entry.value: getattr(self._api.arguments, entry.value)
            for entry in api_name.value.arguments
        }  
        # Create a parameter string including any parameters for the endpoint which have a defined value
        parm_string = "&".join(
            f"{entry.value}={getattr(self._api.parameters, entry.value)}"
            for entry in api_name.value.parms
            if getattr(self._api.parameters, entry.value) is not None
        )        
        # Create a URL from the supplied information
        url = f"{self._api.url}/{api_name.value.endpoint.format(**arguments)}/?{parm_string}"             
        # Call the API endpoint and return the results
        return api_name.value.response(**self._rest_request(url, api_name.value.auth))

    def _rest_request(self, url: str, auth: bool = False) -> dict:
        """Use the requests module to call the REST API and check the response."""
        # Only pass the API key if it is required
        authorisation = HTTPBasicAuth(self._user, self._passwd) if auth else None
        # Initialize an empty dict for the response
        response = {}
        # Iterate while we have a valid url in order to handle the requirement for multiple queries
        while url is not None:
            try:
                results = self._session.get(url=url, auth=authorisation, timeout=60)
                results.raise_for_status()
                # Check the REST API response status
            except requests.exceptions.RequestException as err:
                self.logger.error(f"Requests error encountered: {err}")
                raise err
            results_json = results.json()
            self.logger.debug("Formatted API results:\n %s", ujson.dumps(results_json, indent=2))
            # If this is the first result then return the json data
            if not response:
                response = results_json
            # Otherwise we are adding to an existing dict and we should concatenate the results
            else:
                response["results"] += results_json["results"]
                response["count"] +=  results_json["count"]
            # If we are told this is not the last response in a list then we need to iterate
            if "next" in results_json:
                url = results_json["next"]
            # Otherwise end the iteration
            else:
                break
        return response

    def _is_current(self, entry: dict) -> bool:
        """Determine if an entry is current based on the valid_from and valid_to fields."""
        from_date = getattr(entry, APIConstants.VALID_FROM.value)           
        return self._is_between(entry, datetime.now(timezone.utc))

    def _is_between(self, entry: dict, time: datetime) -> bool:
        """Determine if an entry is the correct one based on the valid_from and valid_to fields."""
        from_date = getattr(entry, APIConstants.VALID_FROM.value)        
        to_date = getattr(entry, APIConstants.VALID_TO.value)           
        return (from_date is None or from_date <= time) and (to_date is None or to_date >= time)
