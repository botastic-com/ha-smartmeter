"""Sample API Client."""

from __future__ import annotations

import asyncio
import socket
import time
from serial import SerialException
import serial_asyncio

import aiohttp
import async_timeout
import botastic_smartmeter.mbus_decode

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import LOGGER

DEFAULT_BAUDRATE = 115200
DEFAULT_BYTESIZE = serial_asyncio.serial.EIGHTBITS
DEFAULT_PARITY = serial_asyncio.serial.PARITY_NONE
DEFAULT_STOPBITS = serial_asyncio.serial.STOPBITS_ONE
DEFAULT_XONXOFF = False
DEFAULT_RTSCTS = False
DEFAULT_DSRDTR = False
SIM_DATA = "68FAFA6853FF000167DB084B464D675000000981F8200000002388D5AB4F97515AAFC6B88D2F85DAA7A0E3C0C40D004535C397C9D037AB7DBDA329107615444894A1A0DD7E85F02D496CECD3FF46AF5FB3C9229CFE8F3EE4606AB2E1F409F36AAD2E50900A4396FC6C2E083F373233A69616950758BFC7D63A9E9B6E99E21B2CBC2B934772CA51FD4D69830711CAB1F8CFF25F0A329337CBA51904F0CAED88D61968743C8454BA922EB00038182C22FE316D16F2A9F544D6F75D51A4E92A1C4EF8AB19A2B7FEAA32D0726C0ED80229AE6C0F7621A4209251ACE2B2BC66FF0327A653BB686C756BE033C7A281F1D2A7E1FA31C3983E15F8FD16CC5787E6F517166814146853FF110167419A3CFDA44BE438C96F0E38BF83D98316"  # pylint: disable=line-too-long


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
        self._reader = None
        self.data_received = None
        self.mbus_decode = botastic_smartmeter.mbus_decode.MBusDecode(self._mbus_key)
        self.device_info = {
            "serial_number": "123456",
            "sw_version": "1.0",
            "hw_version": "1.0",
        }
        # self._serial_loop_task = None
        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(self._serial_port)
        )

    async def async_open_port(self, **kwargs) -> any:
        """Open port from the API."""
        return await serial_asyncio.open_serial_connection(
            url=self._serial_port,
            baudrate=self._baudrate,
            bytesize=self._bytesize,
            parity=self._parity,
            stopbits=self._stopbits,
            xonxoff=self._xonxoff,
            rtscts=self._rtscts,
            dsrdtr=self._dsrdtr,
            **kwargs,
        )

    async def async_close_port(self) -> None:
        """Close port from the API."""
        if self._reader is not None:
            await self._reader.close()

    async def async_get_data(self) -> any:
        """Get data from the API."""
        return await self._api_wrapper()

    async def _api_wrapper(self) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                if self.data_received == None:
                    return self.mbus_decode.message_decode(SIM_DATA, False)
                else:
                    return self.data_received
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
            LOGGER.info("Try to stop serial_loop_task...")
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
                (self._reader, _) = await self.async_open_port(**kwargs)

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

                while True:
                    chars_to_read = self._reader.in_waiting
                    if chars_to_read > 0:
                        try:
                            in_hex = self._reader.read(chars_to_read).decode("ascii")
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
                                    self.data_received = (
                                        self.mbus_decode.message_decode(
                                            message_buffer, False
                                        )
                                    )
                                    if self.data_received:
                                        self._hass.coordinator.async_set_updated_data(
                                            self.data_received
                                        )
                                    else:
                                        LOGGER.exception("Error in data decryption")
                    else:
                        time.sleep(0.1)

    async def _handle_error(self):
        """Handle error for serial connection."""
        await asyncio.sleep(1)
