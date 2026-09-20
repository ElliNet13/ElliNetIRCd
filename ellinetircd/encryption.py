# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

from __future__ import annotations

from pathlib import Path
import io
import logging
from typing import Optional, Union
import secrets
import string

from cryptography.fernet import Fernet

logger = logging.getLogger("ellinetircd.encryption")

KEY_PATH = Path("./DO_NOT_SHARE.key")

if KEY_PATH.exists():
    with KEY_PATH.open("rb") as f:
        KEY = f.read()
else:
    logger.info("Generating encryption key")
    KEY = Fernet.generate_key()
    with KEY_PATH.open("wb") as f:
        f.write(KEY)

FERNET = Fernet(KEY)

class EncryptedFile(io.IOBase):
    """A file-like object that transparently encrypts and decrypts its contents."""

    def __init__(
        self,
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
    ) -> None:
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding or "utf-8"
        self.binary = "b" in mode

        if "x" in mode and self.path.exists():
            raise FileExistsError(self.path)

        # Read an existing encrypted file.
        if "r" in mode or "+" in mode or "a" in mode:
            if self.path.exists():
                encrypted = self.path.read_bytes()
                data = FERNET.decrypt(encrypted)
            else:
                if "r" in mode and "+" not in mode and "a" not in mode:
                    raise FileNotFoundError(self.path)

                data = b""
        else:
            data = b""

        # "w" truncates the file.
        if "w" in mode:
            data = b""

        self._buffer = io.BytesIO(data)

        # Append mode starts at the end.
        if "a" in mode:
            self._buffer.seek(0, io.SEEK_END)

    def close(self) -> None:
        if self.closed:
            return

        # Write the encrypted contents back to disk.
        if any(flag in self.mode for flag in ("w", "a", "+", "x")):
            data = self._buffer.getvalue()
            encrypted = FERNET.encrypt(data)
            self.path.write_bytes(encrypted)

        self._buffer.close()
        super().close()

    def read(self, size: int = -1) -> str | bytes:
        data = self._buffer.read(size)

        if self.binary:
            return data

        return data.decode(self.encoding)

    def read1(self, size: int = -1) -> str | bytes:
        return self.read(size)

    def readline(self, size: int = -1) -> str | bytes:
        data = self._buffer.readline(size)

        if self.binary:
            return data

        return data.decode(self.encoding)

    def readlines(self, hint: int = -1) -> list[str] | list[bytes]:
        data = self._buffer.readlines(hint)

        if self.binary:
            return data

        return [line.decode(self.encoding) for line in data]

    def write(self, data: str | bytes) -> int:
        if self.binary:
            if not isinstance(data, bytes):
                raise TypeError(
                    "a bytes-like object is required, not 'str'"
                )

            return self._buffer.write(data)

        if not isinstance(data, str):
            raise TypeError(
                "write() argument must be str, not bytes"
            )

        return self._buffer.write(data.encode(self.encoding))

    def writelines(self, lines) -> None:
        for line in lines:
            self.write(line)

    def seek(
        self,
        offset: int,
        whence: int = io.SEEK_SET,
    ) -> int:
        return self._buffer.seek(offset, whence)

    def tell(self) -> int:
        return self._buffer.tell()

    def truncate(self, size: Optional[int] = None) -> int:
        return self._buffer.truncate(size)

    def readable(self) -> bool:
        return "r" in self.mode or "+" in self.mode

    def writable(self) -> bool:
        return any(flag in self.mode for flag in ("w", "a", "x", "+"))

    def seekable(self) -> bool:
        return True

    def flush(self) -> None:
        # Nothing needs to be written until close().
        pass

    @property
    def closed(self) -> bool:
        return self._buffer.closed


def open_encrypted(
    path: Union[str, Path],
    mode: str = "r",
    encoding: Optional[str] = None,
) -> EncryptedFile:
    """Open an encrypted file."""
    return EncryptedFile(path, mode, encoding)

def generate_password(length: int = 64) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))