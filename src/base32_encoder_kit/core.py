"""RFC 4648 Base32 encoding and decoding.

The implementation is deliberately strict about the alphabet and padding,
but deliberately lenient about case. RFC 4648 defines the alphabet in
uppercase, yet many systems (URLs, user input, configuration files) emit
lowercase. We normalise case before decoding so callers do not have to.

An optional checksum mode appends a single Base32 character that is the
XOR of the raw decoded bytes, reduced modulo 32. This is not a strong
integrity check; it is a cheap typo detector. It is off by default so that
plain RFC 4648 output is byte-for-byte compatible with other libraries.
"""

from __future__ import annotations

__all__ = ["Base32Error", "decode", "encode"]

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_DECODE_TABLE = {ch: i for i, ch in enumerate(_ALPHABET)}
# Lowercase variants are folded in so that decode() accepts either case.
for _ch, _i in list(_DECODE_TABLE.items()):
    _DECODE_TABLE[_ch.lower()] = _i


class Base32Error(ValueError):
    """Raised when input is not valid Base32 or the checksum does not match."""


def _checksum_char(raw: bytes) -> str:
    """Return the Base32 character representing the XOR of *raw*.

    XOR of an empty sequence is defined as 0, which keeps the checksum of
    the empty string well-defined rather than special-cased at call sites.
    """
    acc = 0
    for byte in raw:
        acc ^= byte
    return _ALPHABET[acc & 0x1F]


def encode(data: bytes, *, checksum: bool = False) -> str:
    """Encode *data* as RFC 4648 Base32.

    If *checksum* is true, one extra Base32 character is appended. The
    checksum is computed over the raw bytes before padding, so it is
    independent of the encoded length.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    raw = bytes(data)

    bits = 0
    value = 0
    out: list[str] = []
    for byte in raw:
        value = (value << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            out.append(_ALPHABET[(value >> bits) & 0x1F])
    if bits:
        out.append(_ALPHABET[(value << (5 - bits)) & 0x1F])

    # Pad to a multiple of 8 characters as required by RFC 4648 section 6.
    while len(out) % 8:
        out.append("=")

    encoded = "".join(out)
    if checksum:
        encoded += _checksum_char(raw)
    return encoded


def decode(text: str, *, checksum: bool = False) -> bytes:
    """Decode a Base32 string (case-insensitive) back to bytes.

    Padding is required to be present and correct: a string whose length is
    not a multiple of 8 (before any checksum character) is rejected. This
    matches the strict reading of RFC 4648 and avoids silently accepting
    truncated input.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")

    body = text
    expected_checksum: str | None = None
    if checksum:
        if not body:
            raise Base32Error("checksum requested but input is empty")
        body, expected_checksum = body[:-1], body[-1]

    if len(body) % 8 != 0:
        raise Base32Error("invalid length: not a multiple of 8")

    # Strip trailing padding, but only the padding that belongs there.
    unpadded = body.rstrip("=")
    pad_count = len(body) - len(unpadded)
    if pad_count > 6:
        raise Base32Error("too much padding")
    if pad_count and "=" in unpadded:
        raise Base32Error("padding in the middle of input")

    bits = 0
    value = 0
    out = bytearray()
    for ch in unpadded:
        try:
            digit = _DECODE_TABLE[ch]
        except KeyError:
            raise Base32Error(f"invalid character: {ch!r}") from None
        value = (value << 5) | digit
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((value >> bits) & 0xFF)

    # Any leftover bits must be zero, otherwise the input was not produced
    # by a canonical encoder and we cannot round-trip it faithfully.
    if bits and (value & ((1 << bits) - 1)):
        raise Base32Error("non-zero trailing bits")

    raw = bytes(out)
    if checksum:
        assert expected_checksum is not None
        if _checksum_char(raw).upper() != expected_checksum.upper():
            raise Base32Error("checksum mismatch")
    return raw
