# base32_encoder_kit

RFC 4648 Base32 encoding and decoding with case-insensitive input and an optional
single-character checksum.

```python
from base32_encoder_kit import encode, decode, Base32Error

encoded = encode(b"foobar")
assert encoded == "MZXW6YTBOI======"
assert decode(encoded) == b"foobar"

# Lowercase input is accepted.
assert decode("mzxw6ytboi======") == b"foobar"

# Optional checksum: one extra Base32 character, XOR of the raw bytes.
checked = encode(b"foobar", checksum=True)
assert decode(checked, checksum=True) == b"foobar"

try:
    decode("MZXW6")
except Base32Error as exc:
    print(exc)  # invalid length: not a multiple of 8
```

The package exports exactly three names: `encode`, `decode`, and `Base32Error`.

## Why this exists

Most Base32 libraries are either permissive to the point of silently accepting
truncated or corrupted input, or strict to the point of rejecting lowercase
text that a human copied out of a URL. This library takes one clear position:
case is normalised, everything else is validated. Padding must be present and
correct, characters must come from the RFC 4648 alphabet, and any leftover bits
must be zero. That makes `decode(encode(x)) == x` hold for every input, which is
the property most callers actually depend on.

The checksum mode is deliberately weak. It is a single Base32 character equal
to the XOR of the raw bytes reduced modulo 32. It catches single-character
typos and transpositions in short identifiers; it is not a MAC and should not
be used to detect adversarial tampering. It is off by default so that output
remains byte-for-byte compatible with other RFC 4648 implementations.

## The awkward edge

Padding is required. `decode("MZXW6")` raises `Base32Error` because the length
is not a multiple of 8. Many encoders in the wild omit padding; if you need to
accept that, strip the input to a multiple of 8 before calling `decode`, and
remember that you are then choosing to accept ambiguous input. This library
will not make that choice for you.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

