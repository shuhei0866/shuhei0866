import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.update_stats import update_card, validate_card


VALID = b'''<svg xmlns="http://www.w3.org/2000/svg">
<text data-testid="stars">22</text><text data-testid="commits">632</text>
<text data-testid="prs">157</text><text data-testid="issues">49</text>
<text data-testid="contribs">14</text></svg>\n'''
ERROR = b'''<svg xmlns="http://www.w3.org/2000/svg">
<text data-testid="message">Cannot read properties of undefined (reading 'user')</text>
</svg>'''


class UpdateStatsTests(unittest.TestCase):
    def test_error_card_does_not_replace_last_good_image(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "stats.svg"
            destination.write_bytes(VALID)
            with patch("scripts.update_stats.urllib.request.urlopen",
                       side_effect=lambda *args, **kwargs: io.BytesIO(ERROR)), \
                    patch("scripts.update_stats.time.sleep"):
                with self.assertRaises(ValueError):
                    update_card(destination)
            self.assertEqual(destination.read_bytes(), VALID)

    def test_transient_error_retries_then_saves_valid_card(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "stats.svg"
            with patch("scripts.update_stats.urllib.request.urlopen",
                       side_effect=[io.BytesIO(ERROR), io.BytesIO(VALID)]), \
                    patch("scripts.update_stats.time.sleep"):
                update_card(destination)
            self.assertEqual(destination.read_bytes(), VALID)

    def test_missing_and_non_numeric_stats_are_rejected(self):
        for value in (b'', b'undefined', b'1,', b'1,,2', b'12,34'):
            data = VALID.replace(b'632', value)
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_card(data)

    def test_grouped_and_compact_counts_are_accepted(self):
        for value in (b'0', b'1,234', b'12,345,678', b'1.2k'):
            with self.subTest(value=value):
                validate_card(VALID.replace(b'632', value))


if __name__ == "__main__":
    unittest.main()
