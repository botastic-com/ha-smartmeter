"""MBUS decode unit for Botastic Smartmeter."""

import xml.etree.ElementTree as ET

from datetime import datetime
from binascii import unhexlify
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
from Cryptodome.Cipher import AES

from . import sensor
from .const import LOGGER


class MBusDecode:
    """Representation of the mbus decode unit"""

    def __init__(self, mbus_key):
        """Initialize the mbus decode unit."""
        self._mbus_key = mbus_key
        self.tr = GXDLMSTranslator()
        # Values in XML File
        self.octet_string_values = {}
        self.conversion_factor = {}
        for entity in sensor.ENTITY_DESCRIPTIONS:
            self.octet_string_values[entity.octet] = entity.key
            self.conversion_factor[entity.key] = entity.conversion_factor

    def evn_decrypt(self, frame, key, system_title, frame_counter):
        """encrypt the frame"""
        frame = unhexlify(frame)
        encryption_key = unhexlify(key)
        init_vector = unhexlify(system_title + frame_counter)
        cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=init_vector)
        return cipher.decrypt(frame).hex()

    def apdu_decode(self, apdu, print_out=False):
        """decode the apdu"""
        if apdu[0:4] != "0f80":
            LOGGER.exception("Error apdu header: %s", apdu[0:4])
            return
        try:
            xml = self.tr.pduToXml(
                apdu,
            )
            # LOGGER.info("xml: ",xml)

            root = ET.fromstring(xml)
            data_received = {}

            items = list(root.iter())
            for i, child in enumerate(items):
                if child.tag == "OctetString" and "Value" in child.attrib:
                    value = child.attrib["Value"]
                    if value in self.octet_string_values:
                        if "Value" in items[i + 1].attrib:
                            key = self.octet_string_values[value]
                            data_received[key] = self.conversion_factor[key] * int(
                                items[i + 1].attrib["Value"], 16
                            )

        except BaseException as err:  # pylint: disable=broad-except
            # LOGGER.info("APU: ", format(apdu))
            LOGGER.warning("adpu decode failed: %s", format(err))
            return

        if print_out:
            now = datetime.now()
            LOGGER.info("\nSmartmeter Output: %s", now.strftime("%d.%m.%Y %H:%M:%S"))
            msg_t = "OBIS Code\t" + f"{"Description":^23}" + "\tValue"
            LOGGER.info(msg_t)
            for entity in sensor.ENTITY_DESCRIPTIONS:
                msg = (
                    entity.octet
                    + "\t"
                    + f"{entity.key + " (" + entity.native_unit_of_measurement + "):":>23}"
                    + "\t"
                )
                LOGGER.info(
                    "%s%s",
                    msg,
                    str(round(data_received[entity.key], 2)),
                )
            msg_p = "------------\t" + f"{"Power overall (W):":>23}" + "\t%s"
            LOGGER.info(
                msg_p,
                str(data_received["power_import"] - data_received["power_export"]),
            )
        return data_received

    def message_decode(self, msg, print_out=False):
        """Decode hex message from mbus."""
        mbusstart = msg[0:8]
        frame_len = int("0x" + mbusstart[2:4], 16)
        system_title = msg[22:38]
        frame_counter = msg[44:52]
        frame = msg[52 : 8 + frame_len * 2]
        apdu = self.evn_decrypt(frame, self._mbus_key, system_title, frame_counter)
        if print_out:
            LOGGER.info("Decode: ")
            LOGGER.info("mbusstart: %s", mbusstart)
            LOGGER.info("frame_len: %s", str(frame_len))
            LOGGER.info("system_title: %s", system_title)
            LOGGER.info("frame_counter: %s", frame_counter)
            LOGGER.info("msg: %s", msg)
            LOGGER.info("key: %s", self._mbus_key)
            LOGGER.info("apdu: %s", apdu)
        return self.apdu_decode(apdu, print_out)
