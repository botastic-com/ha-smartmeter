"""Sample API Client."""
from __future__ import annotations

import asyncio
import socket
import time
from serial import SerialException
import serial_asyncio

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import LOGGER
from .mbus_decode import MBusDecode

DEFAULT_BAUDRATE = 115200
DEFAULT_BYTESIZE = serial_asyncio.serial.EIGHTBITS
DEFAULT_PARITY = serial_asyncio.serial.PARITY_NONE
DEFAULT_STOPBITS = serial_asyncio.serial.STOPBITS_ONE
DEFAULT_XONXOFF = False
DEFAULT_RTSCTS = False
DEFAULT_DSRDTR = False


class BotasticSmartmeterApiError(Exception):
    """Exception to indicate a general API error."""


class BotasticSmartmeterApiCommunicationError(BotasticSmartmeterApiError):
    """Exception to indicate a communication error."""


class BotasticSmartmeterApi:
    """botastic_smartmeter API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
        serial_port: str,
        mbus_key: str,
    ) -> None:
        """botastic_smartmeter API Client."""
        self._hass = hass
        self._serial_port = serial_port
        self._mbus_key = mbus_key
        self._baudrate = DEFAULT_BAUDRATE
        self._bytesize = DEFAULT_BYTESIZE
        self._parity = DEFAULT_PARITY
        self._stopbits = DEFAULT_STOPBITS
        self._xonxoff = DEFAULT_XONXOFF
        self._rtscts = DEFAULT_RTSCTS
        self._dsrdtr = DEFAULT_DSRDTR
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop_serial_read)

        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(self._serial_port)
        )

    async def async_get_data(self) -> any:
        """Get data from the API."""
        return await self._api_wrapper()

    async def _api_wrapper(self) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                return None

        except asyncio.TimeoutError as exception:
            raise BotasticSmartmeterApiCommunicationError(
                "Timeout error fetching information",
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise BotasticSmartmeterApiCommunicationError(
                "Error fetching information",
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise BotasticSmartmeterApiError(
                "Something really wrong happened!"
            ) from exception

    @callback
    def stop_serial_read(self, event):
        """Close resources."""
        del event
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    async def serial_read(
        self,
        device,
        **kwargs,
    ):
        """Read the data from the port."""
        logged_error = False
        while True:
            try:
                reader, _ = await serial_asyncio.open_serial_connection(
                    url=device,
                    baudrate=self._baudrate,
                    bytesize=self._bytesize,
                    parity=self._parity,
                    stopbits=self._stopbits,
                    xonxoff=self._xonxoff,
                    rtscts=self._rtscts,
                    dsrdtr=self._dsrdtr,
                    **kwargs,
                )

            except SerialException as exc:
                if not logged_error:
                    LOGGER.exception(
                        "Unable to connect to the serial device %s: %s. Will retry",
                        device,
                        exc,
                    )
                    logged_error = True
                await self._handle_error()
            else:
                LOGGER.info("Serial device %s connected", device)
                data_start = False
                data_nr = 0
                data_nr_target = (282 + 6) * 2
                message_buffer = ""
                mbus_decode = MBusDecode(self._mbus_key)

                while True:
                    chars_to_read = reader.in_waiting
                    if chars_to_read > 0:
                        try:
                            in_hex = reader.read(chars_to_read).decode("ascii")
                        except SerialException as exc:
                            LOGGER.exception(
                                "Error while reading serial device %s: %s", device, exc
                            )
                            await self._handle_error()
                            break
                        else:
                            if not data_start:
                                if in_hex[0:4] == "68FA":
                                    data_start = True
                                    data_nr = 0
                                    message_buffer = ""
                            if data_start:
                                data_nr += chars_to_read
                                message_buffer += in_hex
                                if data_nr >= data_nr_target:
                                    data_start = False
                                    # Decode and Print the contents of the serial data
                                    mbus_decode.message_decode(message_buffer, True)

                    else:
                        time.sleep(0.1)

    async def _handle_error(self):
        """Handle error for serial connection."""
        await asyncio.sleep(1)
