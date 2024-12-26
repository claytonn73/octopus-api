"""This code contains dataclasses which enable the construction of REST API clients

RESTClient: The RESTClient data class represents the configuration for making API requests.
It includes information such as the API URL, authentication method, supported API endpoints, arguments, parameters,
and constants. """

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, date, time
from enum import Enum
from typing import get_origin

import ciso8601


@dataclass
class baseclass:
    """This dataclass provides the post_init code to handle the nested dataclasses
    and formatting of datetime entries"""


    def __post_init__(self) -> None:
        for entry in fields(self):
            entry_value = getattr(self, entry.name)
            if entry_value is None:
                continue               
            entry_type = entry.type
            # Order of checks is based on frequency of data within API responses 
            # If the entry type is datetime then convert it from a string to a datetime object
            if entry_type is datetime: 
                setattr(self, entry.name, ciso8601.parse_datetime(entry_value))        
            elif entry_type in {float, str, int, bool}:
                continue
            elif issubclass(entry_type.__class__, range):
                continue
            # If the entry type is date then convert it from a string to a date object
            elif entry_type is date: 
                setattr(self, entry.name, ciso8601.parse_datetime(entry_value).date())
            # If the entry type is time then convert it from a string to a time object
            elif entry_type is time: 
                setattr(self, entry.name, ciso8601.parse_datetime(entry_value).time())                
            # If the entry type is a list
            elif get_origin (entry_type) is list:
                # If the type of the list entry is a dataclass then parse each entry of the list into the dataclass
                if is_dataclass(entry_type.__args__[0]):
                    for index, data in enumerate(entry_value):
                        entry_value[index] = entry_type.__args__[0](**(entry_value[index]))
                # If the type of the list entry is an Enum then convert it to an Enum entry
                if issubclass(entry_type.__args__[0], Enum):
                    try:
                        entry_value[index] = entry_type.__args__[0][data]
                    except KeyError:
                        setattr(self, entry.name, entry_type(entry_value))
                    except TypeError:
                        pass
            # If the entry type is a dataclass and the entry is not null then parse the entry into the dataclass
            elif (is_dataclass(entry_type)) and (bool(entry_value)):
                setattr(self, entry.name, entry_type(**(entry_value)))
            # If the entry type is an Enum then convert it to an Enum entry
            elif issubclass(entry_type, Enum):
                try:
                    setattr(self, entry.name, entry_type[entry_value])
                except KeyError:
                    setattr(self, entry.name, entry_type(entry_value))
                except TypeError:
                    pass
            # If the entry type is a dict and the entry is not null
            elif (get_origin(entry_type) is dict) and (bool(entry_value)):
                # Create a new dict in case we have to change the index
                new_dict = {}
                for index, data in enumerate(entry_value):
                    # if the dict value is a dataclass
                    if is_dataclass(entry_type.__args__[1]):
                        entry_value[data] = entry_type.__args__[1](**(entry_value[data]))
                    # if the dict index is an enum
                    if issubclass(entry_type.__args__[0], Enum):
                        # print(getattr(entry_type.__args__[0], data))
                        new_dict[getattr(entry_type.__args__[0], data)] = entry_value[data]
                        # for index, data in enumerate(entry_value):
                        #    entry_value[index] = entry_type.__args__[0][entry_name]
                    else:
                        new_dict[data] = entry_value[data]
                setattr(self, entry.name, new_dict)


@dataclass(frozen=True)
class Endpoint:
    """Dataclass describing API endpoints and the data they return."""
    response: object
    sample: str = None
    name: str = None
    endpoint: str = ""
    type: str = "get"
    auth: str = None
    arguments: list = field(default_factory=list)
    parms: list = field(default_factory=list)


@dataclass
class APIArguments:
    """Dataclass describing the set of arguments used by the API endpoints."""


@dataclass
class APIParameters:
    """Dataclass describing the set of parameters used by the API endpoints."""


@dataclass
class RESTClient:
    """This dataclass defines the set of information necessary to use a REST API.

    Attributes:
        url: The URL used for the REST API
        auth: The type of authorisation used
        apis: A list of the API Endpoints
        apiargs: A dataclass describing the set of arguments used by the endpoints
        apiparms: A dataclass describing the set of parameters used by the endpoints
        constants: A list of constants
    """
    url: str
    auth: str
    apilist: Enum
    arguments: APIArguments = None
    parameters: APIParameters = None
    constants: Enum = None
