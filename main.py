"""Forward N1MM Logger+ spot broadcasts to a TCI server."""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
from decimal import Decimal, DecimalException
from xml.etree import ElementTree

from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException


LOG = logging.getLogger(__name__)
SPOT_COLOR = 0xFFFFA500
TCI_DELIMITERS = str.maketrans({":": " ", ",": " ", ";": " "})


def spot_command(data: bytes) -> str | None:
    spot = ElementTree.fromstring(data.rstrip(b"\x00"))
    if spot.tag.lower() != "spot":
        return None

    callsign = spot.findtext("dxcall", "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9/\-]+", callsign):
        raise ValueError("invalid callsign")

    action = spot.findtext("action", "add").strip().lower()
    if action == "delete":
        return f"SPOT_DELETE:{callsign};"
    if action != "add":
        return None

    frequency_khz = Decimal(spot.findtext("frequency", "").strip())
    if not frequency_khz.is_finite() or not 0 < frequency_khz < 1_000_000_000:
        raise ValueError("invalid spot frequency")
    frequency_hz = int(round(frequency_khz * 1000))
    if not frequency_hz:
        raise ValueError("invalid spot frequency")

    mode = spot.findtext("mode", "").strip().upper()
    if mode and not re.fullmatch(r"[A-Z0-9+\-]+", mode):
        raise ValueError("invalid mode")
    comment = spot.findtext("comment", "").translate(TCI_DELIMITERS)
    comment = " ".join(comment.split())
    comment = "".join(char if " " <= char <= "~" else "?" for char in comment)
    return f"SPOT:{callsign},{mode},{frequency_hz},{SPOT_COLOR},{comment};"


class SpotReceiver(asyncio.DatagramProtocol):
    def __init__(self, commands: asyncio.Queue[str]):
        self.commands = commands

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            command = spot_command(data)
        except (ElementTree.ParseError, DecimalException, ValueError, LookupError) as exc:
            LOG.debug("Ignoring invalid packet from %s: %s", addr, exc)
            return

        if command is not None:
            if self.commands.full():
                self.commands.get_nowait()
            self.commands.put_nowait(command)


async def send_spots(websocket, commands: asyncio.Queue[str]) -> None:
    while True:
        command = await commands.get()
        await websocket.send(command)
        LOG.info("Forwarded %s", command)


async def forward_spots(url: str, commands: asyncio.Queue[str]) -> None:
    while True:
        try:
            async with connect(url, proxy=None, open_timeout=5) as websocket:
                LOG.info("Connected to TCI at %s", url)
                sender = asyncio.create_task(send_spots(websocket, commands))
                try:
                    async for _ in websocket:
                        pass  # Drain TCI status messages while forwarding spots.
                finally:
                    sender.cancel()
                    await asyncio.gather(sender, return_exceptions=True)
            LOG.warning("TCI disconnected. Retrying in 2 seconds.")
        except (OSError, asyncio.TimeoutError, WebSocketException) as exc:
            LOG.warning("TCI connection failed (%s). Retrying in 2 seconds.", exc)
        await asyncio.sleep(2)


async def run(listen_host: str, listen_port: int, tci_url: str) -> None:
    commands = asyncio.Queue(maxsize=1000)
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: SpotReceiver(commands), local_addr=(listen_host, listen_port)
    )
    LOG.info("Listening for N1MM+ spots on UDP %s:%d", listen_host, listen_port)
    try:
        await forward_spots(tci_url, commands)
    finally:
        transport.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen-host", default="127.0.0.1", help="UDP bind address")
    parser.add_argument("--listen-port", type=int, default=12060, help="UDP port")
    parser.add_argument("--tci-url", default="ws://127.0.0.1:50001", help="TCI WebSocket URL")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(run(args.listen_host, args.listen_port, args.tci_url))
    except KeyboardInterrupt:
        pass
    except OSError as exc:
        parser.exit(1, f"Could not start the UDP listener: {exc}\n")


if __name__ == "__main__":
    main()
