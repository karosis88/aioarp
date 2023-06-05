import time
import typing

from aioarp import _exceptions as exc
from aioarp._arp import ARP_HEADER_SIZE, ETHERNET_HEADER_SIZE, ArpPacket, EthPacket, Protocol
from aioarp._utils import is_valid_ipv4
from aioarp.defaults import DEFAULT_READ_TIMEOUT, DEFAULT_REPLY_MISSING_TIME, DEFAULT_WRITE_TIMEOUT

from .backends._async import AsyncStream

__all__ = (
    'async_send_arp',
)


async def receive_arp(sock: AsyncStream, timeout: float) -> ArpPacket:
    start_time = time.time()
    while True:

        # Check if timeout was expired
        if time.time() - start_time > timeout:
            raise exc.NotFoundError()

        # Try to read frame
        try:
            frame = await sock.receive_frame(timeout=DEFAULT_READ_TIMEOUT)
        except Exception as e:
            raise exc.NotFoundError() from e

        # Extract the ethernet header
        eth_header = frame[:ETHERNET_HEADER_SIZE]

        try:
            eth_packet = EthPacket.parse(eth_header)
            if eth_packet.proto != Protocol.arp:
                continue

            arp_response = ArpPacket.parse(
                frame[ETHERNET_HEADER_SIZE: ETHERNET_HEADER_SIZE + ARP_HEADER_SIZE])
            if is_valid_ipv4(arp_response.sender_ip):
                return arp_response
        except BaseException:
            # TODO: catch concrete errors
            ...


async def async_send_arp(arp_packet: ArpPacket, interface: str, timeout: typing.Optional[float] = None) -> ArpPacket:
    sock = AsyncStream(interface)
    ethernet_packet = EthPacket(
        target_mac=arp_packet.target_mac,
        sender_mac=arp_packet.sender_mac,
        proto=Protocol.arp
    )

    try:
        frame_to_send = ethernet_packet.build_frame() + arp_packet.build_frame()
        await sock.write_frame(frame_to_send, timeout=DEFAULT_WRITE_TIMEOUT)
    except exc.WriteTimeoutError as e:
        raise exc.NotFoundError from e

    return await receive_arp(sock, timeout or DEFAULT_REPLY_MISSING_TIME)