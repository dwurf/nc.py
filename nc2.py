#!/usr/bin/env python

# nc2.py - simulate the netcat command in python2
#
# Copyright (c) 2013-2018 Darren Wurf
#

import socket
import errno
import argparse
import sys
import time
from threading import Thread
from Queue import Queue, Empty

# CLI options parsing
parser = argparse.ArgumentParser(
    description='nc2.py: An implementation of NetCat in python2'
)
parser.add_argument('-l', dest='listen', action='store_const', const=True,
                default=False, help='listen instead of connect')
parser.add_argument('hostname', help='IP or hostname to connect to')
parser.add_argument('port', help='port to connect to')
args = parser.parse_args()

class ReadAsync(object):
    def __init__(self, blocking_function, *args):
        self.args = args
        self.read = blocking_function

        self.thread = Thread(target=self.enqueue)
        self.queue = Queue(1024)
        self.thread.daemon = True

        self.thread.start()

    def enqueue(self):
        while True:
            buf = self.read(*self.args)
            if len(buf):
                self.queue.put(buf)
            else:
                time.sleep(0.1)

    def dequeue(self):
        # Throws an exeption called Empty if there's no data to be read
        return self.queue.get_nowait()

# Networking isn't correct, I'm sure this fails in some cases.
# See http://gogonetlive.com/pdf/gogoNET_LIVE/Martin_Levy.pdf
addr = socket.getaddrinfo(
    args.hostname,
    int(args.port),
    socket.AF_UNSPEC,   # IPv4/IPv6
    socket.SOCK_STREAM, # Only TCP
    0                   # No flags
)

family = addr[0][0]     # int representing family eg ipv4/ipv6
socktype = addr[0][1]   # int representing socket type eg tcp/udp
proto = addr[0][2]      # int representing protocol eg ssh (22)
sockaddr = addr[0][4]

if args.listen:
    # Accept connection
    s = socket.socket(family, socktype)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(sockaddr)
    s.listen(1)
    conn, addr = s.accept()
else:
    conn = socket.socket(family, socktype)
    conn.connect(sockaddr)

conn.setblocking(0)
stdin = ReadAsync(sys.stdin.readline)

while True:
    try:
        sys.stdout.write(conn.recv(4096))
    except socket.error as e:
        # POSIX: this error is raised to indicate no data available
        if e.errno != errno.EWOULDBLOCK:
            raise
    try:
        conn.send(stdin.dequeue())
    except Empty:
        time.sleep(0.1)

conn.close()
