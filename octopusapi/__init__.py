"""Octupus energy API client ."""
import logging
from .api import OctopusClient


# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
