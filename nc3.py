#!/usr/bin/env python

# nc3.py - simulate the netcat command in python3
# 
# Copyright (c) 2013-2018 Darren Wurf
# 

import sys
import socket
import argparse
import selectors

# CLI options parsing
parser = argparse.ArgumentParser(
    description='nc3.py: An implementation of NetCat in python3'
)
parser.add_argument('-l', dest='listen', action='store_const', const=True,
                default=False, help='listen instead of connect')
parser.add_argument('hostname', help='IP or hostname to connect to')
parser.add_argument('port', help='port to connect to')

class NetCat():
    def __init__(self, hostname, port, listen=False):
        self._conn = socket.create_connection(
            (args.hostname, int(args.port)))

        self.sel = selectors.DefaultSelector()
        self.sel.register(self._conn, selectors.EVENT_READ,
                          self._read_socket)
        self.sel.register(sys.stdin.buffer.raw, selectors.EVENT_READ,
                          self._write_socket)
        
    def _read_socket(self, conn, mask):
        'Data received from socket, dump to stdout'
        data = self._conn.recv(4096)
        if data:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        else:
            self.unregister()

    def _write_socket(self, stdin, mask):
        'Data received from stdin, dump to socket'
        data = sys.stdin.buffer.read1(4096)

        if data:
            self._conn.sendall(data)
        else:
            self.unregister()

    def unregister(self):
        self.sel.close()

    def run(self):
        while self.sel.get_map() and len(self.sel.get_map()):
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

        self._conn.close()

if __name__ == '__main__':
    args = parser.parse_args()
    
    nc = NetCat(args.hostname, int(args.port))
    nc.run()

