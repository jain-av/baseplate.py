import unittest
from unittest import mock

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from baseplate.lib import metrics
from baseplate.sidecars import SerializedBatch, trace_publisher


class ZipkinPublisherTest(unittest.TestCase):
    @mock.patch("requests.Session", autospec=True)
    def setUp(self, mock_Session):
        self.session = mock_Session.return_value
        self.session.headers = {}
        self.metrics_client = mock.MagicMock(autospec=metrics.Client)
        self.zipkin_api_url = "http://test.local/api/v2"
        self.publisher = trace_publisher.ZipkinPublisher(self.zipkin_api_url, self.metrics_client)

    def test_initialization(self):
        self.assertEqual(self.publisher.endpoint, f"{self.zipkin_api_url}/spans")
        self.publisher.session.mount.assert_called_with("http://", mock.ANY)

    def test_empty_batch(self):
        self.publisher.publish(SerializedBatch(item_count=0, serialized=b""))
        self.assertEqual(self.session.post.call_count, 0)

    def test_publish_retry(self):
        # raise two errors and then return a mock response
        adapter = HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.1))
        self.session.mount("http://", adapter)
        self.session.post.side_effect = [requests.exceptions.ConnectionError, requests.exceptions.Timeout, mock.Mock()]
        spans = b"[]"
        self.publisher.publish(SerializedBatch(item_count=1, serialized=spans))
        self.assertEqual(self.session.post.call_count, 1)
