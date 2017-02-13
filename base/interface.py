#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import urllib


def test(params):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 31001))
    s.sendall(pack_params(params))
    s.close()


def pack_params(params):
    encoded_params = urllib.parse.urlencode(params).encode()
    data = len(encoded_params).to_bytes(4, byteorder='big')
    data += encoded_params
    return data
