"""RFC 4648 Base32 encoder and decoder.

Exports:
    encode(data, *, checksum=False) -> str
    decode(text, *, checksum=False) -> bytes
    Base32Error
"""

from .core import Base32Error, decode, encode

__all__ = ["Base32Error", "decode", "encode"]
