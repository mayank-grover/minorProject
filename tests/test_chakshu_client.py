"""Unit tests for CHAKSHU client SDK interface."""

import unittest
from unittest.mock import patch, MagicMock
from client.chakshu_client import ChakshuImageDescriber, ChakshuClientError

class TestChakshuClient(unittest.TestCase):
    def setUp(self):
        self.client = ChakshuImageDescriber(base_url="http://127.0.0.1:8000", token="test-token")

    @patch("urllib.request.urlopen")
    def test_health_check(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "ok", "model_ready": true}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        health = self.client.check_health()
        self.assertEqual(health["status"], "ok")
        self.assertTrue(health["model_ready"])

    @patch("urllib.request.urlopen")
    def test_describe_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"description": "A sunflower.", "inference_ms": 3200}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = self.client.describe(
            image_url="https://thumb.wikimedia.org/sunflower.jpg",
            article_title="Common sunflower",
            caption="A bright sunflower"
        )
        self.assertEqual(res["description"], "A sunflower.")
        self.assertEqual(res["inference_ms"], 3200)

if __name__ == "__main__":
    unittest.main()
