# Originally from aioircd
# Copyright (c) 2020 Julien Castiaux
# Original work licensed under the MIT License.
#
# Copyright (c) 2026 ElliNet13
# Modifications licensed under the GNU General Public License v3.0 or later.

import socket
import os

def notify(payload: bytes) -> None:
    if _sdsocket:
        _sdsocket.sendall(payload)


def ready() -> None:
    notify(b"READY=1")


def reloading() -> None:
    notify(b"RELOADING=1")


def stopping() -> None:
    notify(b"STOPPING=1")


def status(line: str) -> None:
    notify(b"STATUS=" + line.encode())


# Setup
_sdsocket = None
_notify_socket = os.getenv('NOTIFY_SOCKET', '')
if _notify_socket:
    if _notify_socket.startswith('@'):
        _notify_socket = f'\0{_notify_socket[1:]}'

    if hasattr(socket, "AF_UNIX"):
        family = socket.AF_UNIX # pyright: ignore[reportAttributeAccessIssue]
    else:
        # Platform/Python build doesn't provide Unix-domain sockets.
        family = socket.AF_INET
    
    _sdsocket = socket.socket(family, socket.SOCK_DGRAM)
    _sdsocket.connect(_notify_socket)
