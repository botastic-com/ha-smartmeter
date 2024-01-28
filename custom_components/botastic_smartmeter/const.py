"""Constants for botastic_smartmeter."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "botastic smartmeter"
DOMAIN = "botastic_smartmeter"
VERSION = "1.0.0"
ATTRIBUTION = "Data provided by https://www.botastic.com/"

CONF_MBUS_KEY = "mbus_key"
CONF_SERIAL_PORT = "serial_port"
