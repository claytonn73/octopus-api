"""Dataclass definitions which describe the Octopus API."""
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List
from enum import Enum
import dateutil.parser


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


class Constants(Enum):
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
    GAS_PRODUCT_CODE = "gas_product_code"
    GAS_TARIFF_CODE = "gas_tariff_code"
    PRODUCT_CODE = "product_code"
    TARIFF_CODE = "tariff_code"
    # EXPORT_PRODUCT_CODE = "export_product_code"
    # EXPORT_TARIFF_CODE = "export_tariff_code"


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
    gas_product_code: str = None
    gas_tariff_code: str = None
    product_code: str = None
    tariff_code: str = None
    # export_product_code: str = None
    # export_tariff_code: str = None


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
class meterpoint:
    gsp: str
    mpan: str
    profile_class: str


@dataclass
class register:
    identifier: str
    rate: str
    is_settlement_register: bool


@dataclass
class electricity_meter:
    serial_number: str
    registers: List[register]

    def __post_init__(self):
        for index, entry in enumerate(self.registers):
            if isinstance(entry, dict):
                self.registers[index] = register(**self.registers[index])


@dataclass
class gas_meter:
    serial_number: str


@dataclass
class agreement:
    tariff_code: str
    valid_from: datetime
    valid_to: datetime

    def __post_init__(self):
        if self.valid_from is not None:
            self.valid_from = dateutil.parser.parse(self.valid_from)
        if self.valid_to is not None:
            self.valid_to = dateutil.parser.parse(self.valid_to)


@dataclass
class electricity_meter_point:
    mpan: str
    profile_class: int
    meters: List[electricity_meter]
    agreements: List[agreement]
    is_export: bool = False
    consumption_day: int = 0
    consumption_night: int = 0
    consumption_standard: int = 0

    def __post_init__(self):
        for index, entry in enumerate(self.meters):
            if isinstance(entry, dict):
                self.meters[index] = electricity_meter(**self.meters[index])
        for index, entry in enumerate(self.agreements):
            if isinstance(entry, dict):
                self.agreements[index] = agreement(**self.agreements[index])


@dataclass
class gas_meter_point:
    mprn: str
    consumption_standard: int
    meters: List[gas_meter]
    agreements: List[agreement]

    def __post_init__(self):
        for index, entry in enumerate(self.meters):
            if isinstance(entry, dict):
                self.meters[index] = gas_meter(**self.meters[index])
        for index, entry in enumerate(self.agreements):
            if isinstance(entry, dict):
                self.agreements[index] = agreement(**self.agreements[index])


@dataclass
class property:
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

    def __post_init__(self):
        for index, entry in enumerate(self.electricity_meter_points):
            if isinstance(entry, dict):
                self.electricity_meter_points[index] = electricity_meter_point(**self.electricity_meter_points[index])
        for index, entry in enumerate(self.gas_meter_points):
            if isinstance(entry, dict):
                self.gas_meter_points[index] = gas_meter_point(**self.gas_meter_points[index])
        if self.moved_in_at is not None:
            self.moved_in_at = dateutil.parser.parse(self.moved_in_at)
        if self.moved_out_at is not None:
            self.moved_out_at = dateutil.parser.parse(self.moved_out_at)


@dataclass
class account:
    number: str = ""
    properties: List[property] = field(default_factory=list)
    # regionid is not part of API response but is added with separate query
    regionid: str = ""

    def __post_init__(self):
        for index, entry in enumerate(self.properties):
            if isinstance(entry, dict):
                self.properties[index] = property(**self.properties[index])


@dataclass
class usagegroup:
    date: datetime.date
    consumption: float = 0
    pricerange: PriceType = PriceType.STANDARD


@dataclass
class groupedusage:
    date: datetime.date
    usage: list[usagegroup] = field(default_factory=list)


@dataclass
class usagedata:
    consumption: float
    interval_start: datetime
    interval_end: datetime

    def __post_init__(self):
        self.interval_start = dateutil.parser.parse(self.interval_start)
        self.interval_end = dateutil.parser.parse(self.interval_end)


@dataclass
class usage:
    count: int
    next: str
    previous: str
    results: List[usagedata]

    def __post_init__(self):
        for index, entry in enumerate(self.results):
            if isinstance(entry, dict):
                self.results[index] = usagedata(**self.results[index])


@dataclass
class link:
    href: str
    method: str
    rel: str


@dataclass
class productsdata:
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

    def __post_init__(self):
        for index, entry in enumerate(self.links):
            if isinstance(entry, dict):
                self.links[index] = link(**self.links[index])
        if self.available_from is not None:
            self.available_from = dateutil.parser.parse(self.available_from)
        if self.available_to is not None:
            self.available_to = dateutil.parser.parse(self.available_to)


@dataclass
class products:
    count: int
    next: str
    previous: str
    results: List[productsdata]

    def __post_init__(self):
        for index, entry in enumerate(self.results):
            if isinstance(entry, dict):
                self.results[index] = productsdata(**self.results[index])


@dataclass
class supplypoint:
    code: str
    count: int
    next: str
    previous: str
    results: List[str]


@dataclass(order=True)
class rate:
    value_exc_vat: float
    value_inc_vat: float
    valid_from: datetime
    valid_to: datetime
    payment_method: str = None

    def __post_init__(self):
        if self.valid_from is not None:
            self.valid_from = dateutil.parser.parse(self.valid_from)
        if self.valid_to is not None:
            self.valid_to = dateutil.parser.parse(self.valid_to)


@dataclass
class rates:
    count: int
    next: str
    previous: str
    results: List[rate]

    def __post_init__(self):
        for index, entry in enumerate(self.results):
            if isinstance(entry, dict):
                self.results[index] = rate(**self.results[index])


@dataclass
class tariff:
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

    def __post_init__(self):
        for index, entry in enumerate(self.links):
            if isinstance(entry, dict):
                self.links[index] = link(**self.links[index])


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
class quote_type:
    electricity_single_rate: rate_cost
    electricity_dual_rate: rate_cost = None
    dual_fuel_single_rate: rate_cost = None
    dual_fuel_dual_rate: rate_cost = None

    def __post_init__(self):
        self.electricity_single_rate = rate_cost(**self.electricity_single_rate)
        if self.electricity_dual_rate is not None:
            self.electricity_dual_rate = rate_cost(**self.electricity_dual_rate)
        if self.dual_fuel_single_rate is not None:
            self.dual_fuel_single_rate = rate_cost(**self.dual_fuel_single_rate)
        if self.dual_fuel_dual_rate is not None:
            self.dual_fuel_dual_rate = rate_cost(**self.dual_fuel_dual_rate)


@dataclass
class sample_quote:
    direct_debit_monthly: quote_type
    direct_debit_quarterly: quote_type = None

    def __post_init__(self):
        self.direct_debit_monthly = quote_type(**self.direct_debit_monthly)
        if self.direct_debit_quarterly is not None:
            self.direct_debit_quarterly = quote_type(**self.direct_debit_quarterly)


@dataclass
class rate_type:
    electricity_standard: int = 0
    electricity_day: int = 0
    electricity_night: int = 0
    gas_standard: int = 0


@dataclass
class sample_consumption:
    electricity_single_rate: rate_type = None
    electricity_dual_rate: rate_type = None
    dual_fuel_single_rate: rate_type = None
    dual_fuel_dual_rate: rate_type = None

    def __post_init__(self):
        if self.electricity_single_rate is not None:
            self.electricity_single_rate = rate_type(**self.electricity_single_rate)
        if self.electricity_dual_rate is not None:
            self.electricity_dual_rate = rate_type(**self.electricity_dual_rate)
        if self.dual_fuel_single_rate is not None:
            self.dual_fuel_single_rate = rate_type(**self.dual_fuel_single_rate)
        if self.dual_fuel_dual_rate is not None:
            self.dual_fuel_dual_rate = rate_type(**self.dual_fuel_dual_rate)


@dataclass
class product:
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
    sample_consumption: dict
    links: List[link]

    def __post_init__(self):
        for index, entry in enumerate(self.links):
            if isinstance(entry, dict):
                self.links[index] = link(**self.links[index])
        for index, entry in enumerate(self.single_register_electricity_tariffs):
            self.single_register_electricity_tariffs[entry] = tariff_type(**self.single_register_electricity_tariffs[entry]) # noqa
        for index, entry in enumerate(self.dual_register_electricity_tariffs):
            self.dual_register_electricity_tariffs[entry] = tariff_type(**self.dual_register_electricity_tariffs[entry])
        for index, entry in enumerate(self.single_register_gas_tariffs):
            self.single_register_gas_tariffs[entry] = tariff_type(**self.single_register_gas_tariffs[entry])
        for index, entry in enumerate(self.sample_quotes):
            self.sample_quotes[entry] = sample_quote(**self.sample_quotes[entry])
        self.sample_consumption = sample_consumption(**self.sample_consumption)
        for index, entry in enumerate(self.links):
            if isinstance(entry, dict):
                self.links[index] = link(**self.links[index])
        if self.available_from is not None:
            self.available_from = dateutil.parser.parse(self.available_from)
        if self.available_to is not None:
            self.available_to = dateutil.parser.parse(self.available_to)
        if self.tariffs_active_at is not None:
            self.tariffs_active_at = dateutil.parser.parse(self.tariffs_active_at)


@dataclass
class Api:
    """Dataclass describing Octopus API endpoints and the data they return."""
    response: dataclass
    type: str = "get"
    auth: bool = False
    endpoint: str = ""
    arguments: list = field(default_factory=list)
    parms: list = field(default_factory=list)


Account = Api(auth=True,
              endpoint="v1/accounts/{account}",
              arguments=[APIArgs.ACCOUNT],
              response=account)

Products = Api(endpoint="v1/products",
               parms=[APIParms.IS_PREPAY, APIParms.IS_GREEN, APIParms.IS_TRACKER,
                      APIParms.IS_BUSINESS, APIParms.AVAILABLE_AT, APIParms.PAGE],
               response=products)

Product = Api(endpoint="v1/products/{product_code}",
              arguments=[APIArgs.PRODUCT_CODE],
              parms=[APIParms.TARIFFS_ACTIVE_AT],
              response=product)

SupplyPoints = Api(endpoint="v1/industry/grid-supply-points",
                   parms=[APIParms.POSTCODE],
                   response=supplypoint)

ElectricityMeterPoints = Api(endpoint="v1/electricity-meter-points/{mpan}",
                             arguments=[APIArgs.MPAN],
                             response=meterpoint)

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
    endpoint="v1/products/{gas_product_code}/gas-tariffs/{gas_tariff_code}/standing-charges",
    arguments=[APIArgs.GAS_PRODUCT_CODE, APIArgs.GAS_TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

GasStandardUnitRates = Api(
    endpoint="v1/products/{gas_product_code}/gas-tariffs/{gas_tariff_code}/standard-unit-rates",
    arguments=[APIArgs.GAS_PRODUCT_CODE, APIArgs.GAS_TARIFF_CODE],
    parms=[APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.PAGE_SIZE],
    response=rates)

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
    endpoint="v1/electricity-meter-points/{export_mpan}/meters/{electricity_serial_number}/consumption",
    arguments=[APIArgs.EXPORT_MPAN, APIArgs.ELECTRICITY_SERIAL_NUMBER],
    parms=[APIParms.PAGE_SIZE, APIParms.PERIOD_FROM, APIParms.PERIOD_TO, APIParms.ORDER_BY, APIParms.GROUP_BY],
    response=usage)


@dataclass
class RESTClient:
    url: str
    auth: str
    apis: dict[str, Api]
    constants: dict[str, str]


# class Octopus(Enum):
#    URL = "https://api.octopus.energy"
#    AUTH = "HTTPBasicAuth"
#    ACCOUNT = Account


Octopus = RESTClient(
    url="https://api.octopus.energy",
    auth="HTTPBasicAuth",
    apis={
        "Account": Account,
        "GasConsumption": GasConsumption,
        "ElectricityConsumption": ElectricityConsumption,
        "ElectricityExport": ElectricityExport,
        "SupplyPoints": SupplyPoints,
        "ElectricityMeterPoints": ElectricityMeterPoints,
        "Product": Product,
        "Products": Products,
        "ElectricityStandingCharges": ElectricityStandingCharges,
        "ElectricityStandardUnitRates": ElectricityStandardUnitRates,
        "ElectricityDayUnitRates": ElectricityDayUnitRates,
        "ElectricityNightUnitRates": ElectricityNightUnitRates,
        "GasStandingCharges": GasStandingCharges,
        "GasStandardUnitRates": GasStandardUnitRates,
    },
    constants={
        "RegionID": RegionID,
        "Direction": Direction,
        "Rate": Rate,
    }
)
