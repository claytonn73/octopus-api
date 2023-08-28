"""Dataclass definitions which describe the Octopus API."""
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, get_origin

import dateutil.parser
from requests.auth import HTTPBasicAuth


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


@dataclass
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


@dataclass
class apiparms:
    period_from: datetime = (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%dT%H:%MZ')
    period_to: datetime = datetime.now().strftime('%Y-%m-%dT%H:%MZ')
    page_size: int = 100
    order_by: str = Order.FORWARD.value
    group_by: str = Group.DAY.value
    postcode: str = None
    tariffs_active_at: datetime = datetime.now().strftime('%Y-%m-%dT%H:%MZ')
    is_prepay: bool = False
    is_variable: bool = False
    is_green: bool = False
    is_tracker: bool = False
    is_business: bool = False
    available_at: datetime = datetime.now().strftime('%Y-%m-%dT%H:%MZ')
    page: int = 1
    account: str = None


@dataclass
class Api:
    """Dataclass describing Octopus API endpoints and the data they return."""
    response: dataclass
    type: str = "get"
    auth: bool = False
    endpoint: str = ""
    arguments: list = field(default_factory=list)
    parms: list = field(default_factory=list)


@dataclass
class baseclass:
    """This dataclass provides the post_init code to handle the nested dataclasses
    and formatting of datetime entries"""

    def __post_init__(self):
        for entry in fields(self):
            # If the entry type is datetime then convert it from a string to a datetime object
            if entry.type == datetime:
                if getattr(self, entry.name) is not None:
                    setattr(self, entry.name, dateutil.parser.parse(getattr(self, entry.name)))
            # If the entry type is a dataclass then parse the entry into the dataclass
            if is_dataclass(entry.type):
                # Handle cases where the entry might not exist
                if getattr(self, entry.name) is not None:
                    setattr(self, entry.name, entry.type(**(getattr(self, entry.name))))
            # If the entry type is a list
            if get_origin(entry.type) == list:
                # If the type of the list entry is a dataclass then parse each entry of the list into the dataclass
                if is_dataclass(entry.type.__args__[0]):
                    for index, data in enumerate(getattr(self, entry.name)):
                        getattr(self, entry.name)[index] = entry.type.__args__[0](**(getattr(self, entry.name)[index]))


@dataclass
class register:
    identifier: str
    rate: str
    is_settlement_register: bool


@dataclass
class electricity_meter(baseclass):
    serial_number: str
    registers: List[register]


@dataclass
class gas_meter:
    serial_number: str


@dataclass
class agreement(baseclass):
    tariff_code: str
    valid_from: datetime
    valid_to: datetime


@dataclass
class electricity_meter_point(baseclass):
    mpan: str
    profile_class: int
    meters: List[electricity_meter]
    agreements: List[agreement]
    is_export: bool = False
    consumption_day: int = 0
    consumption_night: int = 0
    consumption_standard: int = 0


@dataclass
class gas_meter_point(baseclass):
    mprn: str
    consumption_standard: int
    meters: List[gas_meter]
    agreements: List[agreement]


@dataclass
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
    electricity_meter_points: List[electricity_meter_point] = field(default_factory=list)
    gas_meter_points: List[gas_meter_point] = field(default_factory=list)


@dataclass
class account(baseclass):
    number: str = ""
    properties: List[property] = field(default_factory=list)
    # regionid is not part of API response but is added with separate query
    regionid: str = ""


Account = Api(auth=True,
              endpoint="v1/accounts/{account}",
              arguments=[APIArgs.ACCOUNT],
              response=account)


@dataclass
class supplypoint(baseclass):
    code: str
    count: int
    next: str
    previous: str
    results: List[RegionID]


SupplyPoints = Api(endpoint="v1/industry/grid-supply-points",
                   parms=[APIParms.POSTCODE],
                   response=supplypoint)


@dataclass
class link:
    href: str
    method: str
    rel: str


@dataclass
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


@dataclass
class products(baseclass):
    count: int
    next: str
    previous: str
    results: List[productsdata]


Products = Api(endpoint="v1/products",
               parms=[APIParms.IS_PREPAY, APIParms.IS_GREEN, APIParms.IS_TRACKER,
                      APIParms.IS_BUSINESS, APIParms.AVAILABLE_AT, APIParms.PAGE],
               response=products)


@dataclass
class tariff(baseclass):
    code: str
    standard_unit_rate_exc_vat: float
    standard_unit_rate_inc_vat: float
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


@dataclass
class tariff_type:
    direct_debit_monthly: tariff = field(default_factory=dict)
    direct_debit_quarterly: tariff = field(default_factory=dict)

    def __post_init__(self):
        self.direct_debit_monthly = tariff(**self.direct_debit_monthly)
        if self.direct_debit_quarterly != {}:
            self.direct_debit_quarterly = tariff(**self.direct_debit_quarterly)


@dataclass
class rate_cost:
    annual_cost_inc_vat: int
    annual_cost_exc_vat: int


@dataclass
class quote_type(baseclass):
    electricity_single_rate: rate_cost
    electricity_dual_rate: rate_cost = None
    dual_fuel_single_rate: rate_cost = None
    dual_fuel_dual_rate: rate_cost = None


@dataclass
class sample_quote(baseclass):
    direct_debit_monthly: quote_type
    direct_debit_quarterly: quote_type = None


@dataclass
class rate_type:
    electricity_standard: int = 0
    electricity_day: int = 0
    electricity_night: int = 0
    gas_standard: int = 0


@dataclass
class sample_consumption_data(baseclass):
    electricity_single_rate: rate_type = None
    electricity_dual_rate: rate_type = None
    dual_fuel_single_rate: rate_type = None
    dual_fuel_dual_rate: rate_type = None


@dataclass
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
    single_register_electricity_tariffs: dict
    dual_register_electricity_tariffs: dict
    single_register_gas_tariffs: dict
    sample_quotes: dict
    sample_consumption: sample_consumption_data
    links: List[link]


Product = Api(endpoint="v1/products/{product_code}",
              arguments=[APIArgs.PRODUCT_CODE],
              parms=[APIParms.TARIFFS_ACTIVE_AT],
              response=product)


@dataclass
class meterpoint:
    gsp: str
    mpan: str
    profile_class: str


ElectricityMeterPoints = Api(endpoint="v1/electricity-meter-points/{mpan}",
                             arguments=[APIArgs.MPAN],
                             response=meterpoint)


@dataclass(order=True)
class rate(baseclass):
    value_exc_vat: float
    value_inc_vat: float
    valid_from: datetime
    valid_to: datetime
    payment_method: str = None


@dataclass
class rates(baseclass):
    count: int
    next: str
    previous: str
    results: List[rate]


ElectricityStandingCharges = Api(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/standing-charges",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityStandardUnitRates = Api(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityDayUnitRates = Api(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/day-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

ElectricityNightUnitRates = Api(
    endpoint="v1/products/{product_code}/electricity-tariffs/{tariff_code}/night-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

GasStandingCharges = Api(
    endpoint="v1/products/{product_code}/gas-tariffs/{tariff_code}/standing-charges",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

GasStandardUnitRates = Api(
    endpoint="v1/products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates",
    arguments=[APIArgs.PRODUCT_CODE, APIArgs.TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)


@dataclass
class usagedata(baseclass):
    consumption: float
    interval_start: datetime
    interval_end: datetime


@dataclass
class usage(baseclass):
    count: int
    next: str
    previous: str
    results: List[usagedata]


GasConsumption = Api(
    auth=True,
    endpoint="v1/gas-meter-points/{mprn}/meters/{gas_serial_number}/consumption",
    arguments=[APIArgs.MPRN, APIArgs.GAS_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)


ElectricityConsumption = Api(
    auth=True,
    endpoint="v1/electricity-meter-points/{mpan}/meters/{electricity_serial_number}/consumption",
    arguments=[APIArgs.MPAN, APIArgs.ELECTRICITY_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)

ElectricityExport = Api(
    auth=True,
    endpoint="v1/electricity-meter-points/{export_mpan}/meters/{export_serial_number}/consumption",
    arguments=[APIArgs.EXPORT_MPAN, APIArgs.EXPORT_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)


@dataclass
class usagegroup(baseclass):
    date: datetime.date
    consumption: float = 0
    pricerange: PriceType = PriceType.STANDARD


@dataclass
class groupedusage(baseclass):
    date: datetime.date
    usage: list[usagegroup] = field(default_factory=list)


@dataclass
class RESTClient:
    url: str
    auth: str
    apilist: Enum
    arguments: APIArgs
    parameters: APIParms
    constants: Enum


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


Octopus = RESTClient(
    url="https://api.octopus.energy",
    auth=HTTPBasicAuth,
    apilist=APIList,
    arguments=apiargs(),
    parameters=apiparms(),
    constants=Constants
)
