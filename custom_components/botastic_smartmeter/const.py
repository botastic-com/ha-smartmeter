"""Constants for botastic_smartmeter."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "botastic_smartmeter"
NAME = "Botastic Smartmeter"
MODEL = "botastic smartmeter 1"
VERSION = "1.0.0"
MANUFACTURER = "botastic"
ATTRIBUTION = "Data provided by https://www.botastic.com/"

CONF_SERIAL_PORT = "serial_port"
CONF_SERIAL_PORT_MANUAL = "Enter Manually"
CONF_MBUS_KEY = "mbus_key"
CONF_MBUS_KEY_DEFAULT = "0123456789ABCDEF0123456789ABCDEF"
