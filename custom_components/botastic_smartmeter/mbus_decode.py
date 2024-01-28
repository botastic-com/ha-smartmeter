"""MBUS decode unit for Botastic Smartmeter."""

import xml.etree.ElementTree as ET

from datetime import datetime
from binascii import unhexlify
from gurux_dlms.GXDLMSTranslator import GXDLMSTranslator
from Cryptodome.Cipher import AES

from .const import LOGGER


class MBusDecode:
    """Representation of the mbus decode unit"""

    def __init__(self, mbus_key):
        """Initialize the mbus decode unit."""
        self._mbus_key = mbus_key
        self.tr = GXDLMSTranslator()
        # Werte im XML File
        self.octet_string_values = {}
        self.octet_string_values["0100010800FF"] = "WirkenergieP"
        self.octet_string_values["0100020800FF"] = "WirkenergieN"
        self.octet_string_values["0100010700FF"] = "MomentanleistungP"
        self.octet_string_values["0100020700FF"] = "MomentanleistungN"
        self.octet_string_values["0100200700FF"] = "SpannungL1"
        self.octet_string_values["0100340700FF"] = "SpannungL2"
        self.octet_string_values["0100480700FF"] = "SpannungL3"
        self.octet_string_values["01001F0700FF"] = "StromL1"
        self.octet_string_values["0100330700FF"] = "StromL2"
        self.octet_string_values["0100470700FF"] = "StromL3"
        self.octet_string_values["01000D0700FF"] = "Leistungsfaktor"

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
            return
        try:
            xml = self.tr.pduToXml(
                apdu,
            )
            # LOGGER.info("xml: ",xml)

            root = ET.fromstring(xml)
            found_lines = []
            momentan = []

            items = list(root.iter())
            for i, child in enumerate(items):
                if child.tag == "OctetString" and "Value" in child.attrib:
                    value = child.attrib["Value"]
                    if value in self.octet_string_values:
                        if "Value" in items[i + 1].attrib:
                            if value in ["0100010700FF", "0100020700FF"]:
                                # special handling for momentanleistung
                                momentan.append(int(items[i + 1].attrib["Value"], 16))
                            found_lines.append(
                                {
                                    "key": self.octet_string_values[value],
                                    "value": int(items[i + 1].attrib["Value"], 16),
                                }
                            )

        #        LOGGER.info(found_lines)
        except BaseException as err:
            # LOGGER.info("APU: ", format(apdu))
            LOGGER.exception("Fehler: %s", format(err))
            return
        try:
            if len(momentan) == 2:
                found_lines.append(
                    {"key": "Momentanleistung", "value": momentan[0] - momentan[1]}
                )

            for element in found_lines:
                if element["key"] == "WirkenergieP":
                    wirkenergie_p = element["value"] / 1000
                if element["key"] == "WirkenergieN":
                    wirkenergie_n = element["value"] / 1000

                if element["key"] == "MomentanleistungP":
                    momentanleistung_p = element["value"]
                if element["key"] == "MomentanleistungN":
                    momentanleistung_n = element["value"]

                if element["key"] == "SpannungL1":
                    spannung_l1 = element["value"] * 0.1
                if element["key"] == "SpannungL2":
                    spannung_l2 = element["value"] * 0.1
                if element["key"] == "SpannungL3":
                    spannung_l3 = element["value"] * 0.1

                if element["key"] == "StromL1":
                    strom_l1 = element["value"] * 0.01
                if element["key"] == "StromL2":
                    strom_l2 = element["value"] * 0.01
                if element["key"] == "StromL3":
                    strom_l3 = element["value"] * 0.01

                if element["key"] == "Leistungsfaktor":
                    leistungsfaktor = element["value"] * 0.001

        except BaseException as err:
            LOGGER.exception("Fehler: %s", format(err))
            return

        if print_out:
            now = datetime.now()
            LOGGER.info("\nSmartmeter Output: %s", now.strftime("%d.%m.%Y %H:%M:%S"))
            LOGGER.info("OBIS Code\tBezeichnung\t\t\t Wert")
            LOGGER.info(
                "1.0.32.7.0.255\tSpannung L1 (V):\t\t %s", str(round(spannung_l1, 2))
            )
            LOGGER.info(
                "1.0.52.7.0.255\tSpannung L2 (V):\t\t %s", str(round(spannung_l2, 2))
            )
            LOGGER.info(
                "1.0.72.7.0.255\tSpannung L3 (V):\t\t %s", str(round(spannung_l3, 2))
            )
            LOGGER.info(
                "1.0.31.7.0.255\tStrom L1 (A):\t\t\t %s", str(round(strom_l1, 2))
            )
            LOGGER.info(
                "1.0.51.7.0.255\tStrom L2 (A):\t\t\t %s", str(round(strom_l2, 2))
            )
            LOGGER.info(
                "1.0.71.7.0.255\tStrom L3 (A):\t\t\t %s", str(round(strom_l3, 2))
            )
            LOGGER.info(
                "1.0.1.7.0.255\tWirkleistung Bezug [W]: \t %s", str(momentanleistung_p)
            )
            LOGGER.info(
                "1.0.2.7.0.255\tWirkleistung Lieferung [W]:\t %s",
                str(momentanleistung_n),
            )
            LOGGER.info(
                "1.0.1.8.0.255\tWirkenergie Bezug [kWh]:\t %s", str(wirkenergie_p)
            )
            LOGGER.info(
                "1.0.2.8.0.255\tWirkenergie Lieferung [kWh]:\t %s", str(wirkenergie_n)
            )
            LOGGER.info("-------------\tLeistungsfaktor:\t\t %s", str(leistungsfaktor))
            LOGGER.info(
                "-------------\tWirkleistunggesamt [w]:\t\t %s",
                str(momentanleistung_p - momentanleistung_n),
            )

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
            LOGGER.info(apdu)
        self.apdu_decode(apdu, print_out)
