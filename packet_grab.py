import optirx as rx

dsock = rx.mkdatasock(ip_address='0.0.0.0',multicast_address='239.255.42.99', port=1511)
version = (2, 7, 0, 0)  # NatNet version to use
while True:
    data = dsock.recv(rx.MAX_PACKETSIZE)
    packet = rx.unpack(data, version=version)
    if type(packet) is rx.SenderData:
        version = packet.natnet_version
    print packet 