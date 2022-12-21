"""Constant definitions which describe the Octopus API."""
from datetime import datetime
from enum import Enum


class Products(Enum):
    """API endpoint that returns the list of products."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products"
    ARGUMENTS = {}
    PARMS = {
        "is_variable": bool,
        "is_green": bool,
        "is_tracker": bool,
        "is_prepay": bool,
        "is_business": bool,
        "available_at": datetime,
        "page": int,
    }
    RESPONSE = {
        "count": int,
        "next": str,
        "previous": str,
        "results": list,
    }
    results = {
        "code": str,
        "direction": str,
        "full_name": str,
        "display_name": str,
        "description": str,
        "is_variable": bool,
        "is_green": bool,
        "is_tracker": bool,
        "is_prepay": bool,
        "is_business": bool,
        "is_restricted": bool,
        "term": int,
        "available_from": datetime,
        "available_to": datetime,
        "links": list,
        "brand": str,
    }
    links = {
        "href": "url",
        "method": str,
        "rel": str,
    }


class Product(Enum):
    """API endpoint that returns the details of a product based on the product code provided."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{product_code}"
    ARGUMENTS = {
        "product_code": str,
    }
    PARMS = {
        "tariffs_active_at": datetime,
    }
    RESPONSE = {
        "code": str,
        "full_name": str,
        "display_name": str,
        "description": str,
        "is_variable": bool,
        "is_green": bool,
        "is_tracker": bool,
        "is_prepay": bool,
        "is_business": bool,
        "is_restricted": bool,
        "brand": str,
        "term": int,
        "available_from": datetime,
        "available_to": datetime,
        "tariffs_active_at": datetime,
        "single_register_electricity_tariffs": dict,
        "dual_register_electricity_tariffs": dict,
        "single_register_gas_tariffs": dict,
        "sample_quotes": dict,
        "sample_consumption": dict,
        "links": list,
    }
    links = {
        "href": "url",
        "method": str,
        "rel": str,
    }
    sample_consumption = {
        "electricity_single_rate": dict,
        "electricity_dual_rate": dict,
        "dual_fuel_single_rate": dict,
        "dual_fuel_dual_rate": dict,
    }
    electricity_single_rate = {
        "electricity_standard": int,
    }
    electricity_dual_rate = {
        "electricity_day": int,
        "electricity_night": int,
    }
    dual_fuel_single_rate = {
        "electricity_standard": int,
        "gas_standard": int,
    }
    dual_fuel_dual_rate = {
        "electricity_day": int,
        "electricity_night": int,
        "gas_standard": int,
    }
    sample_quotes = {
        "group_id1": dict,
    }
    single_register_electricity_tariffs = {
        "group_id2": dict,
    }
    dual_register_electricity_tariffs = {
        "group_id3": dict,
    }
    single_register_gas_tariffs = {
        "group_id4": dict,
    }
    group_id1 = {
        "direct_debit_monthly": dict,
        "direct_debit_quarterly": dict,
    }
    group_id2 = {
        "direct_debit_monthly": dict,
        "direct_debit_quarterly": dict,
    }
    group_id3 = {
        "direct_debit_monthly": dict,
        "direct_debit_quarterly": dict,
    }
    group_id4 = {
        "direct_debit_monthly": dict,
        "direct_debit_quarterly": dict,
    }
    direct_debit_monthly = {
        "code": str,
        "standing_charge_exc_vat": float,
        "standing_charge_inc_vat": float,
        "online_discount_exc_vat": float,
        "online_discount_inc_vat": float,
        "dual_fuel_discount_exc_vat": float,
        "dual_fuel_discount_inc_vat": float,
        "exit_fees_exc_vat": float,
        "exit_fees_inc_vat": float,
        "links": list,
        "standard_unit_rate_exc_vat": float,
        "standard_unit_rate_inc_vat": float,
    }


class Account(Enum):
    """API endpoint providing details for an account based on the account number."""

    TYPE = "GET"
    AUTH = True
    ENDPOINT = "v1/accounts/{account}"
    ARGUMENTS = {
        "account": str,
    }
    PARMS = {}
    RESPONSE = {
        "number": str,
        "properties": list,
    }
    properties = {
        "id": int,
        "moved_in_at": datetime,
        "moved_out_at": datetime,
        "address_line_1": str,
        "address_line_2": str,
        "address_line_3": str,
        "town": str,
        "county": str,
        "postcode": str,
        "electricity_meter_points": list,
        "gas_meter_points": list,
    }
    electricity_meter_points = {
        "mpan": str,
        "profile_class": str,
        "consumption_standard": int,
        "meters": list,
        "agreements": list,
        "is_export": bool,
    }
    gas_meter_points = {
        "mprn": str,
        "consumption_standard": int,
        "meters": list,
        "agreements": list,
    }
    meters = {
        "serial_number": str,
        "registers": list,
    }
    registers = {
        "identifier": str,
        "rate": str,
        "is_settlement_register": bool,
    }
    agreements = {
        "tariff_code": str,
        "valid_from": datetime,
        "valid_to": datetime
    }


class SupplyPoints(Enum):
    """API endpoint providing list of grid supply points for a postcode."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/industry/grid-supply-points"
    ARGUMENTS = {}
    PARMS = {
        "postcode": str,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "group_id": str,
    }


class ElectricityMeterPoints(Enum):
    """API endpoint listing the electricity meter points for a mpan."""

    TYPE = "GET"
    AUTH = True
    ENDPOINT = "v1/electricity-meter-points/{mpan}"
    ARGUMENTS = {
        "mpan": str,
    }
    PARMS = {}
    RESPONSE = {
        "gsp": str,
        "mpan": str,
        "profile_class": int,
    }


class ElectricityStandingCharges(Enum):
    """API Endpoint returning standing charges for an electricity product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges"
    ARGUMENTS = {
        "product_code": str,
        "tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class ElectricityStandardUnitRates(Enum):
    """API endpoint providing standard unit rates for a electricity product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates"
    ARGUMENTS = {
        "product_code": str,
        "tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class ElectricityDayUnitRates(Enum):
    """API endpoint providing night unit rates for a electricity product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{product_code}/electricity-tariffs/{tariff_code}/day-unit-rates"
    ARGUMENTS = {
        "product_code": str,
        "tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class ElectricityNightUnitRates(Enum):
    """API endpoint providing nigh unit rates for a electricity product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{product_code}/electricity-tariffs/{tariff_code}/night-unit-rates"
    ARGUMENTS = {
        "product_code": str,
        "tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class GasStandingCharges(Enum):
    """API endpoint providing standing charges for a gas product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{gas_product_code}/gas-tariffs/{gas_tariff_code}/standing-charges"
    ARGUMENTS = {
        "gas_product_code": str,
        "gas_tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class GasStandardUnitRates(Enum):
    """API endpoint providing standard unit rates for a gas product and tariff."""

    TYPE = "GET"
    AUTH = False
    ENDPOINT = "v1/products/{gas_product_code}/gas-tariffs/{gas_tariff_code}/standard-unit-rates"
    ARGUMENTS = {
        "gas_product_code": str,
        "gas_tariff_code": str,
    }
    PARMS = {
        "period_from": datetime,
        "period_to": datetime,
        "page_size": int,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "value_exc_vat": float,
        "value_inc_vat": float,
        "valid_from": datetime,
        "valid_to": datetime,
    }


class ElectricityConsumption(Enum):
    """API endpoint providing electricity consumption details for a mpan and serial number."""

    TYPE = "GET"
    AUTH = True
    ENDPOINT = "v1/electricity-meter-points/{mpan}/meters/{electricity_serial_number}/consumption"
    ARGUMENTS = {
        "mpan": int,
        "electricity_serial_number": str,
    }
    PARMS = {
        "page_size": int,
        "period_from": datetime,
        "period_to": datetime,
        "order_by": str,
        "group_by": str,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "consumption": float,
        "interval_start": datetime,
        "interval_end": datetime,
    }


class ElectricityExport(Enum):
    """API endpoint providing electricity export details for a mpan and serial number ."""

    TYPE = "GET"
    AUTH = True
    ENDPOINT = "v1/electricity-meter-points/{export_mpan}/meters/{electricity_export_serial_number}/consumption"
    ARGUMENTS = {
        "export_mpan": int,
        "electricity_export_serial_number": str,
    }
    PARMS = {
        "page_size": int,
        "period_from": datetime,
        "period_to": datetime,
        "order_by": str,
        "group_by": str,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "consumption": float,
        "interval_start": datetime,
        "interval_end": datetime,
    }


class GasConsumption(Enum):
    """API endpoint providing gas consumption details for a mprn and serial number."""

    TYPE = "GET"
    AUTH = True
    ENDPOINT = "v1/gas-meter-points/{mprn}/meters/{gas_serial_number}/consumption"
    ARGUMENTS = {
        "mprn": int,
        "gas_serial_number": str,
    }
    PARMS = {
        "page_size": int,
        "period_from": datetime,
        "period_to": datetime,
        "order_by": str,
        "group_by": str,
    }
    RESPONSE = {
        "count": int,
        "next": "url",
        "previous": "url",
        "results": list,
    }
    results = {
        "consumption": float,
        "interval_start": datetime,
        "interval_end": datetime,
    }


class Octopus(Enum):
    """Base class for Octopus API with list of endpoints and their enum classes."""

    URL = "https://api.octopus.energy"
    API_LIST = {
        "Products": Products,
        "Product": Product,
        "Account": Account,
        "SupplyPoints": SupplyPoints,
        "ElectricityMeterPoints": ElectricityMeterPoints,
        "ElectricityStandingCharges": ElectricityStandingCharges,
        "ElectricityStandardUnitRates": ElectricityStandardUnitRates,
        "ElectricityDayUnitRates": ElectricityDayUnitRates,
        "ElectricityNightUnitRates": ElectricityNightUnitRates,
        "GasStandingCharges": GasStandingCharges,
        "GasStandardUnitRates": GasStandardUnitRates,
        "ElectricityConsumption": ElectricityConsumption,
        "ElectricityExport": ElectricityExport,
        "GasConsumption": GasConsumption,
    }
