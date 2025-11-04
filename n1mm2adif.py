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
    now = contact.get("timestamp", "000-00-00 00:00:00")
    station_callsign = contact.get("stationprefix", "").upper()
    cabrillo_name = contact.get("contestname", "contestname")
    filename = str(Path.home()) + "/" + f"{station_callsign}_adif_export.adi"

    # Create file with header if it does not exist already.
    if os.path.exists(filename) is False:
        with open(filename, "w", encoding="utf-8", newline="") as file_descriptor:
            print("N1MM2ADIF export", end="\r\n", file=file_descriptor)
            print("<ADIF_VER:5>3.1.5", end="\r\n", file=file_descriptor)
            print("<EOH>", end="\r\n", file=file_descriptor)

    try:
        with open(filename, "a", encoding="utf-8", newline="") as file_descriptor:
            hiscall = contact.get("call", "")
            hisname = contact.get("name", "")
            the_date_and_time = now
            themode = contact.get("mode", "")
            if themode in ("CW", "CW-U", "CW-L", "CW-R", "CWR"):
                themode = "CW"
            if cabrillo_name in ("CQ-WW-RTTY", "WEEKLY-RTTY"):
                themode = "RTTY"
            frequency = str(Decimal(str(contact.get("rxfreq", 0))) / 100000)
            band = get_adif_band(Decimal(str(contact.get("rxfreq", 0))) / 100000)
            sentrst = contact.get("snt", "")
            rcvrst = contact.get("rcv", "")
            sentnr = str(contact.get("sntnr", "0"))
            rcvnr = str(contact.get("rcvnr", "0"))
            grid = contact.get("gridsquare", "")
            pfx = contact.get("wpxprefix", "")
            comment = contact.get("comment", "")
            loggeddate = the_date_and_time[:10]
            loggedtime = (
                the_date_and_time[11:13]
                + the_date_and_time[14:16]
                + the_date_and_time[17:20]
            )
            print(
                f"<QSO_DATE:{len(''.join(loggeddate.split('-')))}>"
                f"{''.join(loggeddate.split('-'))}",
                end="\r\n",
                file=file_descriptor,
            )

            try:
                print(
                    f"<TIME_ON:{len(loggedtime)}>{loggedtime}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                print(
                    f"<STATION_CALLSIGN:{len(station_callsign)}>{station_callsign}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                print(
                    f"<CALL:{len(hiscall)}>{hiscall.upper()}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                if len(hisname):
                    print(
                        f"<NAME:{len(hisname)}>{hisname.title()}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                if themode in ("USB", "LSB"):
                    print(
                        f"<MODE:3>SSB\r\n<SUBMODE:{len(themode)}>{themode}",
                        end="\r\n",
                        file=file_descriptor,
                    )
                else:
                    print(
                        f"<MODE:{len(themode)}>{themode}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                print(
                    f"<BAND:{len(band)}>{band}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                print(
                    f"<FREQ:{len(frequency)}>{frequency}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                print(
                    f"<RST_SENT:{len(sentrst)}>{sentrst}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                print(
                    f"<RST_RCVD:{len(rcvrst)}>{rcvrst}",
                    end="\r\n",
                    file=file_descriptor,
                )
            except TypeError:
                ...

            try:
                if cabrillo_name in ("WFD", "ARRL-FD", "ARRL-FIELD-DAY"):
                    sent = contact.get("SentExchange", "")
                    if sent:
                        print(
                            f"<STX_STRING:{len(sent)}>{sent.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                elif cabrillo_name in ("ICWC-MST"):
                    sent = f'{contact.get("SentExchange", "")} {sentnr}'
                    if sent:
                        print(
                            f"<STX_STRING:{len(sent)}>{sent.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                elif sentnr != "0":
                    print(
                        f"<STX_STRING:{len(sentnr)}>{sentnr}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            # SRX STRING, Contest dependent
            try:
                # ----------Medium Speed Test------------
                if cabrillo_name in ("ICWC-MST"):
                    rcv = f"{hisname.upper()} {contact.get('NR', '')}"
                    if len(rcv) > 1:
                        print(
                            f"<SRX_STRING:{len(rcv)}>{rcv.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                # ----------Field Days------------
                elif cabrillo_name in ("WFD", "ARRL-FD", "ARRL-FIELD-DAY"):
                    rcv = f"{contact.get('Exchange1', '')} {contact.get('Sect', '')}"
                    if len(rcv) > 1:
                        print(
                            f"<SRX_STRING:{len(rcv)}>{rcv.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                # ------------CQ 160---------------
                elif cabrillo_name in ("CQ-160-CW", "CQ-160-SSB", "WEEKLY-RTTY"):
                    rcv = f"{contact.get('Exchange1', '')}"
                    if len(rcv) > 1:
                        print(
                            f"<SRX_STRING:{len(rcv)}>{rcv.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                # --------------K1USN-SST-----------
                elif cabrillo_name == "K1USN-SST":
                    rcv = f"{contact.get('Name', '')} {contact.get('Sect', '')}"
                    if len(rcv) > 1:
                        print(
                            f"<SRX_STRING:{len(rcv)}>{rcv.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                # ------------CQ-WW-DX-RTTY---------
                elif cabrillo_name == "CQ-WW-RTTY":
                    rcv = f"{str(contact.get('ZN', '')).zfill(2)} {contact.get('Exchange1', 'DX')}"
                    if len(rcv) > 1:
                        print(
                            f"<SRX_STRING:{len(rcv)}>{rcv.upper()}",
                            end="\r\n",
                            file=file_descriptor,
                        )
                elif rcvnr != "0":
                    print(
                        f"<SRX_STRING:{len(rcvnr)}>{rcvnr}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                result = re.match(
                    "[A-R][A-R]([0-9][0-9][A-X][A-X])*([0-9][0-9])?",
                    grid,
                    re.IGNORECASE,
                )
                grid = ""
                if result:
                    grid = result.group()

                if len(grid[:8]) > 1:
                    print(
                        f"<GRIDSQUARE:{len(grid[:8])}>{grid[:8]}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                if len(pfx) > 0:
                    print(
                        f"<PFX:{len(pfx)}>{pfx}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                if len(cabrillo_name) > 1:
                    print(
                        f"<CONTEST_ID:{len(cabrillo_name)}>{cabrillo_name}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            try:
                if len(comment):
                    print(
                        f"<COMMENT:{len(comment)}>{comment}",
                        end="\r\n",
                        file=file_descriptor,
                    )
            except TypeError:
                ...

            print("<EOR>", end="\r\n", file=file_descriptor)
            print("", end="\r\n", file=file_descriptor)
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
