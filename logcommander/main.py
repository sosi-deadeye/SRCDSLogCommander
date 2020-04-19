#!/usr/bin/env python3

"""
Beschreibung
"""

import asyncio
import datetime
import string
import re
from pathlib import Path

from valve import rcon


WHITESPACE = (string.whitespace + "\x00").encode("ascii")
LOG_CMD = re.compile(
    r"RL (?P<month>\d{2})\/(?P<day>\d{2})\/(?P<year>\d{4}) - "
    r"(?P<hour>\d{2}):"
    r"(?P<minute>\d{2}):"
    r"(?P<second>\d{2}):\s+\""
    r"(?P<name>[\w\d\W]+)<"
    r"(?P<id>\d{1,3})><"
    r"(?P<steamid>STEAM_\d:\d:\d{5,10})><"
    r"(?P<team>\w{1,10})>\"\s+say\s+\""
    r"(?P<command>![\w\W]+)\""
)
COMMANDS = {
    cmd.stem: cmd
    for cmd in Path("commands").glob("*.cfg")
}


class LogMsgProtocol(asyncio.BaseProtocol):
    def __call__(self):
        return self

    def connection_made(self, transport):
        self.transport = transport

    @staticmethod
    def datagram_received(data: bytes, addr: str):
        data = data.lstrip(b"\xff").rstrip(WHITESPACE)
        message = data.decode()
        match = LOG_CMD.search(message)
        if match:
            result = match.groupdict()
            timestamp = map(
                int,
                (
                    result["year"],
                    result["month"],
                    result["day"],
                    result["hour"],
                    result["minute"],
                    result["second"],
                ),
            )
            timestamp = datetime.datetime(*timestamp)
            # saddr = f"{addr[0]}:{addr[1]}"
            # print(f"{timestamp} / Received {result['command']} from {saddr}")
            loop = asyncio.get_event_loop()
            loop.run_in_executor(
                None,
                handle_command,
                timestamp,
                result["steamid"],
                addr,
                result["command"],
            )


def handle_command(timestamp, steamid, address, command):
    command = command[1:]
    print(timestamp, steamid, address, command)
    if command in COMMANDS:
        code = COMMANDS[command].read_text()
        rcon.execute(address, "123", code)


async def main():
    loop = asyncio.get_event_loop()
    server = LogMsgProtocol()
    transport, protocol = await loop.create_datagram_endpoint(
        server, local_addr=("5.9.16.40", 8888)
    )
    try:
        await asyncio.sleep(20 * 60)
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main())
