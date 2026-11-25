import os
import socket
import struct

def getNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.connect(('<broadcast>', 0))
    return s.getsockname()[0]

def createV4RequestFrame(logger_sn):
    """Create request frame for inverter logger.

    The request string is build from several parts. The first part is a
    fixed 4 char string; the second part is the reversed hex notation of
    the s/n twice; then again a fixed string of two chars; a checksum of
    the double s/n with an offset; and finally a fixed ending char.

    Args:
        logger_sn (int): Serial number of the inverter

    Returns:
        str: Information request string for inverter
    """
    #frame = (headCode) + (dataFieldLength) + (contrlCode) + (sn) + (sn) + (command) + (checksum) + (endCode)
    frame_hdr = bytes.fromhex('680241b1') #from SolarMan / new Omnik app
    command = bytes.fromhex('0100')
    defchk = bytes.fromhex('87')  # plaatshouder, wordt hieronder door de checksum vervangen
    endCode = bytes.fromhex('16')

    sn = struct.pack('<I', logger_sn)  # serienummer als 4 bytes, little-endian (omgekeerde volgorde)
    frame = bytearray(frame_hdr + sn + sn + command + defchk + endCode)

    # checksum = som van alle bytes behalve de eerste en de laatste twee, modulo 256
    frame[-2] = sum(frame[1:-2]) & 0xFF
    return frame

def expand_path(path):
    """
    Expand relative path to absolute path.

    Args:
        path: file path

    Returns: absolute path to file

    """
    if os.path.isabs(path):
        return path
    else:
        return os.path.dirname(os.path.abspath(__file__)) + "/" + path

def getLoggers():
    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((getNetworkIp(), 48899))
    # Set a timeout so the socket does not block indefinitely when trying to receive data.
    sock.settimeout(3)
    # Set the time-to-live for messages to 1 so they do not go past the local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    SendData = b"WIFIKIT-214028-READ" # Lotto/TM = b"AT+YZAPP=214028,READ"

    gateways = ''
    try:
        # Send data to the broadcast address
        sock.sendto(SendData, ('<broadcast>', 48899))
        # Look for responses from all recipients
        while True:
            try:
                data, server = sock.recvfrom(1024)
            except socket.timeout:
                break
            else:
                if (data == SendData): continue #skip sent data
                a = data.decode('ascii', errors='replace').split(',')
                wifi_ip, wifi_sn = a[0], a[2]  # antwoord: ip,mac,serienummer
                if (len(gateways)>1):
                    gateways = gateways+','
                gateways = gateways+wifi_ip+','+wifi_sn
    finally:
        sock.close()
    return gateways
