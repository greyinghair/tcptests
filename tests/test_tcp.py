"""Exercise TCP echo behavior and AWS SDK compatibility without AWS calls."""

import importlib.util
import logging
import socket
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import boto3
from botocore.stub import Stubber

from tcp_server import handle_client


class EchoTests(unittest.TestCase):
    def check_echo(self, connection_type, messages):
        client, server = socket.socketpair()
        client.settimeout(2)
        worker = threading.Thread(
            target=handle_client,
            args=(server, "local-test", connection_type),
            daemon=True,
        )
        worker.start()
        try:
            for message in messages:
                client.sendall(message)
                received = b""
                while len(received) < len(message):
                    chunk = client.recv(len(message) - len(received))
                    self.assertTrue(chunk, "Server closed before echoing the message")
                    received += chunk
                self.assertEqual(received, message)
            if connection_type == "short-lived":
                self.assertEqual(client.recv(1), b"")
        finally:
            client.close()
            worker.join(timeout=2)
            server.close()
        self.assertFalse(worker.is_alive())

    def test_short_lived_connection_closes_after_echo(self):
        self.check_echo("short-lived", [b"short-lived probe"])

    def test_long_lived_connection_handles_multiple_messages(self):
        self.check_echo("long-lived", [b"heartbeat one", b"heartbeat two"])


class MetricTests(unittest.TestCase):
    def test_metric_payload_is_accepted_by_current_sdk(self):
        # Explicit dummy credentials and Stubber prevent credential discovery and I/O.
        cloudwatch = boto3.client(
            "cloudwatch",
            region_name="eu-west-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        spec = importlib.util.spec_from_file_location(
            "client_under_test", Path(__file__).resolve().parents[1] / "tcp_client.py"
        )
        client = importlib.util.module_from_spec(spec)
        handler = logging.NullHandler()
        with (
            patch("boto3.client", return_value=cloudwatch),
            patch("watchtower.CloudWatchLogHandler", return_value=handler),
            patch("logging.basicConfig"),
        ):
            spec.loader.exec_module(client)
        try:
            with Stubber(cloudwatch) as stubber:
                stubber.add_response(
                    "put_metric_data",
                    {},
                    {
                        "Namespace": "TCPTests",
                        "MetricData": [
                            {
                                "MetricName": f"client_{client.ec2_hostname}_LongLivedConnection",
                                "Value": 1,
                                "Unit": "Count",
                            }
                        ],
                    },
                )
                client.publish_metric("LongLivedConnection", 1)
                stubber.assert_no_pending_responses()
        finally:
            logging.getLogger().removeHandler(handler)
            handler.close()
            cloudwatch.close()
