"""Octupus energy API client ."""
import logging
from .api import OctopusClient # noqa F401

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
