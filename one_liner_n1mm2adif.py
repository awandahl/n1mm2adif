#!/usr/bin/env python3
"""Test multicasting"""
# pylint: disable=invalid-name

import socket
import time
import threading
import queue
import xmltodict
import re
import os

from decimal import Decimal
from pathlib import Path

multicast_port = 12061
multicast_group = "127.0.0.1"
interface_ip = "0.0.0.0"

fifo = queue.Queue()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", multicast_port))
# mreq = socket.inet_aton(multicast_group) + socket.inet_aton(interface_ip)
# s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, bytes(mreq))
s.settimeout(0.1)

def pad_freq(freq: str) -> str:
    if '.' in freq:
        integer, decimal = freq.split('.')
        # Pad with zeros to ensure at least 3 decimals
        if len(decimal) < 3:
            decimal = decimal.ljust(3, '0')
        return f"{integer}.{decimal}"
    else:
        return f"{freq}.000"

def get_adif_band(freq: Decimal) -> str:
    """xxx"""
    if 7500000 >= freq >= 300000:
        return "submm"
    if 250000 >= freq >= 241000:
        return "1mm"
    if 149000 >= freq >= 134000:
        return "2mm"
    if 123000 >= freq >= 119980:
        return "2.5mm"
    if 81000 >= freq >= 75500:
        return "4mm"
    if 47200 >= freq >= 47000:
        return "6mm"
    if 24250 >= freq >= 24000:
        return "1.25cm"
    if 10500 >= freq >= 10000:
        return "3cm"
    if 5925 >= freq >= 5650:
        return "6cm"
    if 3500 >= freq >= 3300:
        return "9cm"
    if 2450 >= freq >= 2300:
        return "13cm"
    if 1300 >= freq >= 1240:
        return "23cm"
    if 928 >= freq >= 902:
        return "33cm"
    if 450 >= freq >= 420:
        return "70cm"
    if 225 >= freq >= 222:
        return "1.25m"
    if 148 >= freq >= 144:
        return "2m"
    if 71 >= freq >= 70:
        return "4m"
    if 69.9 >= freq >= 54.000001:
        return "5m"
    if 54 >= freq >= 50:
        return "6m"
    if 45 >= freq >= 40:
        return "8m"
    if 29.7 >= freq >= 28.0:
        return "10m"
    if 24.99 >= freq >= 24.890:
        return "12m"
    if 21.45 >= freq >= 21.0:
        return "15m"
    if 18.168 >= freq >= 18.068:
        return "17m"
    if 14.35 >= freq >= 14.0:
        return "20m"
    if 10.15 >= freq >= 10.1:
        return "30m"
    if 7.3 >= freq >= 7.0:
        return "40m"
    if 5.45 >= freq >= 5.06:
        return "60m"
    if 4.0 >= freq >= 3.5:
        return "80m"
    if 2.0 >= freq >= 1.8:
        return "160m"
    if 0.504 >= freq >= 0.501:
        return "560m"
    if 0.479 >= freq >= 0.472:
        return "630m"
    if 0.1378 >= freq >= 0.1357:
        return "2190m"
    return "0m"

def gen_adif(contact):
    """
    Creates an ADIF file of the contacts made.
    """
    fields = []
    now = contact.get("timestamp", "000-00-00 00:00:00")
    station_callsign = (contact.get("stationprefix", "") or "").upper()
    cabrillo_name = contact.get("contestname", "contestname") or ""
    filename = str(Path.home()) + "/" + f"{station_callsign}_adif_export.adi"

    # Create file with header if it does not exist already.
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8", newline="") as file_descriptor:
            print("N1MM2ADIF export", file=file_descriptor)
            print("<ADIF_VER:5>3.1.5", file=file_descriptor)
            print("<EOH>", file=file_descriptor)

    try:
        with open(filename, "a", encoding="utf-8", newline="") as file_descriptor:
            hiscall = contact.get("call") or ""
            hisname = contact.get("name") or ""
            the_date_and_time = now

            themode = contact.get("mode") or ""
            if themode in ("CW", "CW-U", "CW-L", "CW-R", "CWR"):
                themode = "CW"
            if cabrillo_name in ("CQ-WW-RTTY", "WEEKLY-RTTY"):
                themode = "RTTY"

            # -- ORIGINAL LOGIC FOR FREQ/BAND HERE --
            frequency = str(Decimal(str(contact.get("rxfreq", 0))) / 100000)
            frequency = pad_freq(frequency)
            band = get_adif_band(Decimal(str(contact.get("rxfreq", 0))) / 100000)

            sentrst = contact.get("snt") or ""
            rcvrst = contact.get("rcv") or ""
            sentnr = str(contact.get("sntnr") or "0")
            rcvnr = str(contact.get("rcvnr") or "0")
            grid = contact.get("gridsquare") or ""
            pfx = contact.get("wpxprefix") or ""
            comment = contact.get("comment") or ""

            loggeddate = the_date_and_time[:10]
            qso_date = ''.join(loggeddate.split('-'))
            loggedtime = (
                the_date_and_time[11:13]
                + the_date_and_time[14:16]
                + the_date_and_time[17:20]
            )

            fields.append(f"<QSO_DATE:{len(qso_date)}>{qso_date}")
            fields.append(f"<TIME_ON:{len(loggedtime)}>{loggedtime}")
            fields.append(f"<STATION_CALLSIGN:{len(station_callsign)}>{station_callsign}")
            fields.append(f"<CALL:{len(hiscall)}>{hiscall.upper()}")
            if len(hisname):
                fields.append(f"<NAME:{len(hisname)}>{hisname.title()}")
            if themode in ("USB", "LSB"):
                fields.append("<MODE:3>SSB")
                fields.append(f"<SUBMODE:{len(themode)}>{themode}")
            else:
                fields.append(f"<MODE:{len(themode)}>{themode}")
            fields.append(f"<BAND:{len(band)}>{band}")
            fields.append(f"<FREQ:{len(frequency)}>{frequency}")
            fields.append(f"<RST_SENT:{len(sentrst)}>{sentrst}")
            fields.append(f"<RST_RCVD:{len(rcvrst)}>{rcvrst}")

            # Sent exchange
            if cabrillo_name in ("WFD", "ARRL-FD", "ARRL-FIELD-DAY"):
                sent = contact.get("SentExchange") or ""
                if sent:
                    fields.append(f"<STX_STRING:{len(sent)}>{sent.upper()}")
            elif cabrillo_name in ("ICWC-MST"):
                sent = f'{contact.get("SentExchange") or ""} {sentnr}'
                if sent.strip():
                    fields.append(f"<STX_STRING:{len(sent.strip())}>{sent.strip().upper()}")
            elif sentnr != "0":
                fields.append(f"<STX_STRING:{len(sentnr)}>{sentnr}")

            # Received exchange
            if cabrillo_name in ("ICWC-MST"):
                rcv = f"{hisname.upper()} {contact.get('NR') or ''}"
                if len(rcv.strip()) > 1:
                    fields.append(f"<SRX_STRING:{len(rcv.strip())}>{rcv.strip().upper()}")
            elif cabrillo_name in ("WFD", "ARRL-FD", "ARRL-FIELD-DAY"):
                ex1 = contact.get("Exchange1") or ""
                sect = contact.get("Sect") or ""
                rcv = f"{ex1} {sect}"
                if len(rcv.strip()) > 1:
                    fields.append(f"<SRX_STRING:{len(rcv.strip())}>{rcv.strip().upper()}")
            elif cabrillo_name in ("CQ-160-CW", "CQ-160-SSB", "WEEKLY-RTTY"):
                ex1 = contact.get("Exchange1") or ""
                if len(ex1) > 1:
                    fields.append(f"<SRX_STRING:{len(ex1)}>{ex1.upper()}")
            elif cabrillo_name == "K1USN-SST":
                name = contact.get("Name") or ""
                sect = contact.get("Sect") or ""
                rcv = f"{name} {sect}"
                if len(rcv.strip()) > 1:
                    fields.append(f"<SRX_STRING:{len(rcv.strip())}>{rcv.strip().upper()}")
            elif cabrillo_name == "CQ-WW-RTTY":
                zn = str(contact.get("ZN") or "")
                ex1 = contact.get("Exchange1") or "DX"
                combined = f"{zn.zfill(2)} {ex1}"
                if len(combined.strip()) > 1:
                    fields.append(f"<SRX_STRING:{len(combined.strip())}>{combined.strip().upper()}")
            elif rcvnr != "0":
                fields.append(f"<SRX_STRING:{len(rcvnr)}>{rcvnr}")

            # Gridsquare
            grid_str = ""
            if grid:
                result = re.match(
                    "[A-R][A-R]([0-9][0-9][A-X][A-X])*([0-9][0-9])?",
                    grid,
                    re.IGNORECASE,
                )
                if result:
                    grid_str = result.group()
            if len(grid_str[:8]) > 1:
                fields.append(f"<GRIDSQUARE:{len(grid_str[:8])}>{grid_str[:8]}")

            if len(pfx):
                fields.append(f"<PFX:{len(pfx)}>{pfx}")
            if len(cabrillo_name) > 1:
                fields.append(f"<CONTEST_ID:{len(cabrillo_name)}>{cabrillo_name}")
            if len(comment):
                fields.append(f"<COMMENT:{len(comment)}>{comment}")
            fields.append("<EOR>")

            # Finally, print your one-liner QSO
            print(" ".join(fields), file=file_descriptor)
    except IOError as error:
        print(f"Error saving ADIF file: {error}")

def watch_udp():
    """watch udp"""
    while True:
        try:
            datagram = s.recv(1500)
        except socket.timeout:
            time.sleep(1)
            continue
        if datagram:
            fifo.put(datagram)


_udpwatch = threading.Thread(
    target=watch_udp,
    daemon=True,
)
_udpwatch.start()

while 1:
    while not fifo.empty():
        packet = xmltodict.parse(fifo.get())
        contact = packet.get("contactinfo", False)
        if contact is not False:
            gen_adif(contact)
    time.sleep(1)
