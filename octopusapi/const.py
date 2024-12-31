"""Dataclass definitions which describe the Octopus API."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List

from requests.auth import HTTPBasicAuth
from octopusapi.apiconstruct import baseclass, RESTClient, Endpoint


class RegionID(Enum):
    _A = "Eastern England"
    _B = "East Midlands"
    _C = "London"
    _D = "Merseyside and Northern Wales"
    _E = "West Midlands"
    _F = "North Eastern England"
    _G = "North Western England"
    _H = "Southern England"
    _J = "South Eastern England"
    _K = "Southern Wales"
    _L = "South Western England"
    _M = "Yorkshire"
    _N = "Southern Scotland"
    _P = "Northern Scotland"


class Direction(Enum):
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"


class PriceType(Enum):
    STANDARD = "Standard"
    PEAK = "Peak"
    OFFPEAK = "OffPeak"


class Rate(Enum):
    STANDARD = "STANDARD"
    ECO7_DAY = "ECO7_DAY"
    ECO7_NIGHT = "ECO7_NIGHT"
    OFF_PEAK = "OFF_PEAK"


class Order(Enum):
    FORWARD = "period"
    BACKWARD = "-period"


class Group(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class APIConstants(Enum):
    VALID_FROM = "valid_from"
    VALID_TO = "valid_to"
    RESULTS = "results"
    COUNT = "count"
    NEXT = "next"
    POSTCODE = "postcode"
    ACCOUNT = "account"
    REGION_ID = "regionid"


class APIArgs(Enum):
    ACCOUNT = "account"
    TARIFF = "tariff"
    PRODUCT = "product"
    MPAN = "mpan"
    MPRN = "mprn"
    EXPORT_MPAN = "export_mpan"
    EXPORT_SERIAL_NUMBER = "export_serial_number"
    ELECTRICITY_SERIAL_NUMBER = "electricity_serial_number"
    GAS_SERIAL_NUMBER = "gas_serial_number"
    PRODUCT_CODE = "product_code"
    TARIFF_CODE = "tariff_code"


@dataclass(slots=True)
class apiargs:
    account: str = None
    tariff: str = None
    product: str = None
    mpan: str = None
    mprn: str = None
    export_mpan: str = None
    export_serial_number: str = None
    electricity_serial_number: str = None
    gas_serial_number: str = None
    product_code: str = None
    tariff_code: str = None


class APIParms(Enum):
    PERIOD_FROM = "period_from"
    PERIOD_TO = "period_to"
    PAGE_SIZE = "page_size"
    ORDER_BY = "order_by"
    GROUP_BY = "group_by"
    POSTCODE = "postcode"
    TARIFFS_ACTIVE_AT = "tariffs_active_at"
    IS_PREPAY = "is_prepay"
    IS_VARIABLE = "is_variable"
    IS_GREEN = "is_green"
    IS_TRACKER = "is_tracker"
    IS_BUSINESS = "is_business"
    AVAILABLE_AT = "available_at"
    PAGE = "page"
    ACCOUNT = "account"

class DatetimeFormat(Enum):
    OCTOPUSDATETIME = '%Y-%m-%dT%H:%MZ'

@dataclass(slots=True)
class apiparms:
    period_from: str = (
        datetime.now()-timedelta(days=1)).strftime(DatetimeFormat.OCTOPUSDATETIME.value)
    period_to: datetime = datetime.now().strftime(DatetimeFormat.OCTOPUSDATETIME.value)
    page_size: int = 9999
    order_by: str = Order.FORWARD.value
    group_by: str = Group.DAY.value
    postcode: str = None
    tariffs_active_at: str = datetime.now().strftime(DatetimeFormat.OCTOPUSDATETIME.value)
    is_prepay: bool = False
    is_variable: bool = False
    is_green: bool = False
    is_tracker: bool = False
    is_business: bool = False
    available_at: str = datetime.now().strftime(DatetimeFormat.OCTOPUSDATETIME.value)
    page: int = 1
    account: str = None


@dataclass(slots=True)
class register:
    identifier: str
    rate: str
    is_settlement_register: bool


@dataclass(slots=True)
class electricity_meter(baseclass):
    serial_number: str
    registers: List[register]


@dataclass(slots=True)
class gas_meter:
    serial_number: str


@dataclass(slots=True)
class agreement(baseclass):
    tariff_code: str
    valid_from: datetime
    valid_to: datetime


@dataclass(slots=True)
class electricity_meter_point(baseclass):
    mpan: str
    profile_class: int
    meters: List[electricity_meter]
    agreements: List[agreement]
    is_export: bool = False
    consumption_day: int = 0
    consumption_night: int = 0
    consumption_standard: int = 0


@dataclass(slots=True)
class gas_meter_point(baseclass):
    mprn: str
    consumption_standard: int
    meters: List[gas_meter]
    agreements: List[agreement]


@dataclass(slots=True)
class property(baseclass):
    id: int
    moved_in_at: datetime
    moved_out_at: datetime
    address_line_1: str
    address_line_2: str
    address_line_3: str
    town: str
    county: str
    postcode: str
    electricity_meter_points: List[electricity_meter_point] = field(
        default_factory=list)
    gas_meter_points: List[gas_meter_point] = field(default_factory=list)


@dataclass(slots=True)
class account(baseclass):
    number: str = ""
    properties: List[property] = field(default_factory=list)
    # regionid is not part of API response but is added with separate query
    regionid: str = ""


Account = Endpoint(auth=True,
                   endpoint="v1/accounts/{account}",
                   arguments=[APIArgs.ACCOUNT],
                   response=account)


@dataclass(slots=True)
class supplypoint(baseclass):
    code: str
    count: int
    next: str
    previous: str
    results: List[RegionID]


SupplyPoints = Endpoint(endpoint="v1/industry/grid-supply-points",
                        parms=[APIParms.POSTCODE],
                        response=supplypoint)


@dataclass(slots=True)
class link:
    href: str
    method: str
    rel: str


@dataclass(slots=True)
class productsdata(baseclass):
    code: str
    direction: str
    full_name: str
    display_name: str
    description: str
    term: int
    available_from: datetime
    available_to: datetime
    brand: str
    links: List[link]
    is_prepay: bool = False
    is_variable: bool = False
    is_green: bool = False
    is_tracker: bool = False
    is_business: bool = False
    is_restricted: bool = False


@dataclass(slots=True)
class products(baseclass):
    count: int
    next: str
    previous: str
    results: List[productsdata]


Products = Endpoint(endpoint="v1/products",
                    parms=[APIParms.IS_PREPAY, APIParms.IS_GREEN, APIParms.IS_TRACKER,
                           APIParms.IS_BUSINESS, APIParms.AVAILABLE_AT, APIParms.PAGE],
                    response=products)


@dataclass(slots=True)
class tariff(baseclass):
    code: str
    standing_charge_exc_vat: float
    standing_charge_inc_vat: float
    online_discount_exc_vat: float
    online_discount_inc_vat: float
    dual_fuel_discount_exc_vat: float
    dual_fuel_discount_inc_vat: float
    exit_fees_exc_vat: float
    exit_fees_inc_vat: float
    exit_fees_type: str
    links: List[link]
    day_unit_rate_exc_vat: float = 0
    day_unit_rate_inc_vat: float = 0
    night_unit_rate_exc_vat: float = 0
    night_unit_rate_inc_vat: float = 0
    standard_unit_rate_exc_vat: float = 0
    standard_unit_rate_inc_vat: float = 0


@dataclass(slots=True)
class tariff_type(baseclass):
    direct_debit_monthly: tariff = field(default_factory=dict)
    direct_debit_quarterly: tariff = field(default_factory=dict)
    varying: tariff = field(default_factory=dict)


@dataclass(slots=True)
class rate_cost:
    annual_cost_inc_vat: int
    annual_cost_exc_vat: int


@dataclass(slots=True)
class quote_type(baseclass):
    electricity_single_rate: rate_cost = None
    electricity_dual_rate: rate_cost = None
    dual_fuel_single_rate: rate_cost = None
    dual_fuel_dual_rate: rate_cost = None


@dataclass(slots=True)
class sample_quote(baseclass):
    direct_debit_monthly: quote_type = None
    direct_debit_quarterly: quote_type = None
    varying: quote_type = None


@dataclass(slots=True)
class rate_type:
    electricity_standard: int = 0
    electricity_day: int = 0
    electricity_night: int = 0
    gas_standard: int = 0


@dataclass(slots=True)
class sample_consumption_data(baseclass):
    electricity_single_rate: rate_type = None
    electricity_dual_rate: rate_type = None
    dual_fuel_single_rate: rate_type = None
    dual_fuel_dual_rate: rate_type = None


@dataclass(slots=True)
class product(baseclass):
    code: str
    full_name: str
    display_name: str
    description: str
    is_variable: bool
    is_green: bool
    is_tracker: bool
    is_prepay: bool
    is_business: bool
    is_restricted: bool
    brand: str
    term: int
    available_from: datetime
    available_to: datetime
    tariffs_active_at: datetime
    single_register_electricity_tariffs: dict[RegionID, tariff_type]
    dual_register_electricity_tariffs: dict[RegionID, tariff_type]
    single_register_gas_tariffs: dict[RegionID, tariff_type]
    sample_quotes: dict[RegionID, sample_quote]
    sample_consumption: sample_consumption_data
    links: List[link]


Product = Endpoint(endpoint="v1/products/{product_code}",
                   arguments=[APIArgs.PRODUCT_CODE],
                   parms=[APIParms.TARIFFS_ACTIVE_AT],
                   response=product)


@dataclass(slots=True)
class meterpoint(baseclass):
    gsp: RegionID
    mpan: str
    profile_class: int


ElectricityMeterPoints = Endpoint(endpoint="v1/electricity-meter-points/{mpan}",
                                  arguments=[APIArgs.MPAN],
                                  response=meterpoint)


@dataclass(slots=True, order=True)
class rate(baseclass):
    value_exc_vat: float
    value_inc_vat: float
    valid_from: datetime
    valid_to: datetime
    payment_method: str = None


@dataclass(slots=True)
class rates(baseclass):
    count: int
    next: str
    previous: str
    results: List[rate]


ElectricityStandingCharges = Endpoint(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityStandardUnitRates = Endpoint(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityDayUnitRates = Endpoint(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/day-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityNightUnitRates = Endpoint(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/night-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

GasStandingCharges = Endpoint(
    endpoint="v1/products/{product_code}/gas-tariffs/{tariff_code}/standing-charges",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

GasStandardUnitRates = Endpoint(
    endpoint="v1/products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)


@dataclass(slots=True)
class usagedata(baseclass):
    consumption: float
    interval_start: datetime
    interval_end: datetime


@dataclass(slots=True)
class usage(baseclass):
    count: int
    next: str
    previous: str
    results: List[usagedata]


GasConsumption = Endpoint(
    auth=True,
    endpoint="v1/gas-meter-points/{mprn}/meters/{gas_serial_number}/consumption",
    arguments=[APIArgs.MPRN, APIArgs.GAS_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM,
           APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)


ElectricityConsumption = Endpoint(
    auth=True,
    endpoint="v1/electricity-meter-points/{mpan}/meters/{electricity_serial_number}/consumption",
    arguments=[APIArgs.MPAN, APIArgs.ELECTRICITY_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM,
           APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)

ElectricityExport = Endpoint(
    auth=True,
    endpoint="v1/electricity-meter-points/{export_mpan}/meters/{export_serial_number}/consumption",
    arguments=[APIArgs.EXPORT_MPAN, APIArgs.EXPORT_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM,
           APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)


@dataclass(slots=True)
class usagegroup(baseclass):
    date: datetime.date
    consumption: float = 0
    pricerange: PriceType = PriceType.STANDARD


@dataclass(slots=True)
class groupedusage(baseclass):
    date: datetime.date
    usage: list[usagegroup] = field(default_factory=list)


class APIList(Enum):
    """This enum lists all the defined API endpoints, making it easy to reference them.
    The Enum value is the instance of the Endpoint class that describes the endpoint.
    """
    Account = Account
    GasConsumption = GasConsumption
    ElectricityConsumption = ElectricityConsumption
    ElectricityExport = ElectricityExport
    SupplyPoints = SupplyPoints
    ElectricityMeterPoints = ElectricityMeterPoints
    Product = Product
    Products = Products
    ElectricityStandingCharges = ElectricityStandingCharges
    ElectricityStandardUnitRates = ElectricityStandardUnitRates
    ElectricityDayUnitRates = ElectricityDayUnitRates
    ElectricityNightUnitRates = ElectricityNightUnitRates
    GasStandingCharges = GasStandingCharges
    GasStandardUnitRates = GasStandardUnitRates


class Constants(Enum):
    """This enum lists all the defined constants, making it easy to reference them."""
    RegionID = RegionID
    Direction = Direction
    PriceType = PriceType
    Rate = Rate
    Order = Order
    Group = Group
    APIConstants = APIConstants
    DateFormat = '%Y-%m-%dT%H:%MZ'


Octopus = RESTClient(
    url="https://api.octopus.energy",
    auth=HTTPBasicAuth,
    apilist=APIList,
    arguments=apiargs(),
    parameters=apiparms(),
    constants=Constants
)
