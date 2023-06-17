import pytest

import aioarp
from aioarp._backends._mock import MockSocket

eth_header_arp = (
    # Eth Header
    b"\x11\x11\x11\x11\x11\x11\x11"
    b"\x11\x11\x11\x11\x11\x08\x06"
)

eth_header_no_arp = (
    # Eth Header
    b"\x11\x11\x11\x11\x11\x11\x11"
    b"\x11\x11\x11\x11\x11\x08\x00"
)

arp_header = (
    # Arp Header
    b"\x00\x01\x08\x00\x06\x04"
    b"\x00\x01\x11\x11\x11\x11"
    b"\x11\x11\x7f\x00\x00\x01"
    b"\x11\x11\x11\x11\x11\x11"
    b"\x7f\x00\x00\x01"
)


@pytest.mark.anyio
def test_async_send_arp():
    msocket = MockSocket(eth_header_arp + arp_header)
    response = aioarp.request('null', '100.100.100.100', sock=msocket)
    assert response
    assert response.sender_mac == '11:11:11:11:11:11'


@pytest.mark.anyio
def test_async_send_arp_timeout():
    with MockSocket(eth_header_no_arp + arp_header) as msocket:
        with pytest.raises(aioarp.NotFoundError):
            aioarp.request('null', '100.100.100.100', sock=msocket, timeout=0.5)
