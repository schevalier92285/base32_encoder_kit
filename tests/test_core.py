import unittest

from base32_encoder_kit import Base32Error, decode, encode


class EncodeTests(unittest.TestCase):
    def test_rfc4648_vectors(self):
        # Test vectors from RFC 4648 section 10.
        vectors = [
            (b"", ""),
            (b"f", "MY======"),
            (b"fo", "MZXQ===="),
            (b"foo", "MZXW6==="),
            (b"foob", "MZXW6YQ="),
            (b"fooba", "MZXW6YTB"),
            (b"foobar", "MZXW6YTBOI======"),
        ]
        for raw, expected in vectors:
            with self.subTest(raw=raw):
                self.assertEqual(encode(raw), expected)

    def test_accepts_bytearray_and_memoryview(self):
        self.assertEqual(encode(bytearray(b"foo")), "MZXW6===")
        self.assertEqual(encode(memoryview(b"foo")), "MZXW6===")

    def test_rejects_str(self):
        with self.assertRaises(TypeError):
            encode("foo")  # type: ignore[arg-type]

    def test_checksum_appends_one_char(self):
        plain = encode(b"foobar")
        checked = encode(b"foobar", checksum=True)
        self.assertEqual(len(checked), len(plain) + 1)
        self.assertTrue(checked.startswith(plain))

    def test_checksum_of_empty_is_xor_zero(self):
        # XOR of no bytes is 0, which maps to 'A'.
        self.assertEqual(encode(b"", checksum=True), "A")


class DecodeTests(unittest.TestCase):
    def test_round_trip(self):
        for raw in [b"", b"f", b"fo", b"foo", b"foob", b"fooba", b"foobar"]:
            with self.subTest(raw=raw):
                self.assertEqual(decode(encode(raw)), raw)

    def test_case_insensitive(self):
        self.assertEqual(decode("mzxw6ytboi======"), b"foobar")
        self.assertEqual(decode("MzXw6YtBoI======"), b"foobar")

    def test_rejects_bad_length(self):
        with self.assertRaises(Base32Error):
            decode("MZXW6")

    def test_rejects_invalid_character(self):
        # '1' is not in the RFC 4648 alphabet (it is excluded to avoid
        # confusion with 'I' and 'L').
        with self.assertRaises(Base32Error):
            decode("MZXW6YTB1======")

    def test_rejects_padding_in_middle(self):
        with self.assertRaises(Base32Error):
            decode("MZ=XW6===")

    def test_rejects_nonzero_trailing_bits(self):
        # 'MZXW6YQ=' decodes to four bytes with two bits left over; flipping
        # the low bit of the final character makes those bits non-zero.
        with self.assertRaises(Base32Error):
            decode("MZXW6YR=")

    def test_rejects_str_type(self):
        with self.assertRaises(TypeError):
            decode(b"MZXW6===")  # type: ignore[arg-type]


class ChecksumTests(unittest.TestCase):
    def test_round_trip_with_checksum(self):
        for raw in [b"", b"f", b"foo", b"foobar", bytes(range(256))]:
            with self.subTest(raw=raw):
                self.assertEqual(decode(encode(raw, checksum=True), checksum=True), raw)

    def test_checksum_mismatch_detected(self):
        good = encode(b"foobar", checksum=True)
        # Replace the checksum character with a different valid one.
        bad = good[:-1] + ("A" if good[-1] != "A" else "B")
        with self.assertRaises(Base32Error):
            decode(bad, checksum=True)

    def test_checksum_is_case_insensitive(self):
        good = encode(b"foobar", checksum=True)
        self.assertEqual(decode(good.lower(), checksum=True), b"foobar")

    def test_checksum_requested_on_empty_input(self):
        with self.assertRaises(Base32Error):
            decode("", checksum=True)


if __name__ == "__main__":
    unittest.main()
