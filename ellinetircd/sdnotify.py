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
    _sdsocket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    _sdsocket.connect(_notify_socket)
