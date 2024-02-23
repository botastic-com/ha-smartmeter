"""Sample API Client."""

from __future__ import annotations

import asyncio
from serial import SerialException
import serial_asyncio
from async_timeout import timeout

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from . import mbus_decode
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
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop_serial_read)
        self._reader = None
        self.coordinator = None
        self.data_received = None
        self.mbus_decode = mbus_decode.MBusDecode(self._mbus_key)
        self.device_info = {
            "serial_number": "123456",
            "sw_version": "1.0",
            "hw_version": "1.0",
        }
        # self._serial_loop_task = None
        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(self._serial_port)
        )

    async def async_open_port(self) -> any:
        """Open port from the API."""
        return await serial_asyncio.open_serial_connection(
            url=self._serial_port,
            baudrate=DEFAULT_BAUDRATE,
            bytesize=DEFAULT_BYTESIZE,
            parity=DEFAULT_PARITY,
            stopbits=DEFAULT_STOPBITS,
            xonxoff=DEFAULT_XONXOFF,
            rtscts=DEFAULT_RTSCTS,
            dsrdtr=DEFAULT_DSRDTR,
        )

    async def async_close_port(self) -> None:
        """Close port from the API."""
        if self._reader is not None:
            await self._reader.close()

    async def async_get_data(self) -> any:
        """Get data from the API."""
        if self.data_received is None:
            return self.mbus_decode.message_decode(SIM_DATA, False)
        return self.data_received

    @callback
    def stop_serial_read(self, event):
        """Close resources."""
        del event
        if self._serial_loop_task:
            LOGGER.info("Try to stop serial_loop_task...")
            self._serial_loop_task.cancel()

    async def serial_read(self, device):
        """Read the data from the port."""
        logged_error = False
        while True:
            try:
                self._reader, _ = await self.async_open_port()

            except SerialException as exc:
                if not logged_error:
                    LOGGER.exception(
                        "Unable to connect to the serial device %s: %s. Will retry",
                        device,
                        exc,
                    )
                    logged_error = True
                await self._handle_error()
            except BaseException as err:  # pylint: disable=broad-except
                LOGGER.exception("Error Open: %s", format(err))
                await self._handle_error()
            else:
                LOGGER.info("Serial device %s connected", device)
                data_start = False
                data_nr = 0
                data_nr_target = (282 + 6) * 2
                message_buffer = ""

                # energy_import_test = 21060.1

                while True:

                    # Testing push function:
                    # self.data_received = self.mbus_decode.message_decode(
                    #     SIM_DATA, False
                    # )
                    # if self.data_received is not None:
                    #     energy_import_test = energy_import_test + 0.1
                    #     self.data_received["energy_import"] = str(energy_import_test)
                    #     self.coordinator.async_set_updated_data(self.data_received)
                    # await asyncio.sleep(2.0)
                    # continue

                    try:
                        async with timeout(2.5):
                            res = await self._reader.read(data_nr_target)
                            in_hex = res.decode("utf-8")
                    except asyncio.TimeoutError:
                        await asyncio.sleep(0.1)
                    except asyncio.exceptions.CancelledError:
                        LOGGER.exception("Cancelled serial read by user")
                        return
                    except SerialException as exc:
                        LOGGER.exception(
                            "Error while reading serial device %s: %s", device, exc
                        )
                        await self._handle_error()
                        break
                    except BaseException as err:  # pylint: disable=broad-except
                        LOGGER.exception("Error Read: %s", format(err))
                        await self._handle_error()
                    else:
                        # LOGGER.debug("read result: %s", in_hex)
                        if in_hex is not None and len(in_hex) > 0:
                            if not data_start:
                                if in_hex[0:4] == "68FA":
                                    data_start = True
                                    data_nr = 0
                                    message_buffer = ""
                            if data_start:
                                data_nr += len(in_hex)
                                message_buffer += in_hex
                                if data_nr >= data_nr_target:
                                    data_start = False
                                    # Decode and Print the contents of the serial data
                                    self.data_received = (
                                        self.mbus_decode.message_decode(
                                            message_buffer, False
                                        )
                                    )
                                    if self.data_received is not None:
                                        self.coordinator.async_set_updated_data(
                                            self.data_received
                                        )
                        else:
                            await asyncio.sleep(0.1)

    async def _handle_error(self):
        """Handle error for serial connection."""
        await asyncio.sleep(1)
