#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import io
import logging
import threading
from contextlib import redirect_stdout
from time import monotonic, sleep
from unittest import TestCase
from unittest.mock import Mock, patch

import thingsboard_gateway.gateway.tb_gateway_service as service_module
from thingsboard_gateway.gateway.tb_gateway_service import TBGatewayService
from thingsboard_gateway.tb_utility.tb_handler import TBRemoteLoggerHandler


class _FakeGateway:
    def __init__(self, max_payload_size):
        self.stopped = False
        self.stop_event = threading.Event()
        self.tb_client = Mock()
        self.tb_client.is_connected.return_value = True
        self.sent = []
        self._max_payload_size = max_payload_size

    def get_max_payload_size_bytes(self):
        return self._max_payload_size

    def send_telemetry(self, telemetry):
        self.sent.append(telemetry)


class TestRemoteLoggerOversizedMessage(TestCase):
    def setUp(self):
        self.gateway = _FakeGateway(max_payload_size=2000)
        self.handler = TBRemoteLoggerHandler(self.gateway)
        self.logger = logging.getLogger('service')
        self.previous_level = self.logger.level
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        self.handler.activate_remote_logging_for_level(logging.INFO)

    def tearDown(self):
        self.gateway.stopped = True
        self.handler.deactivate()
        self.logger.removeHandler(self.handler)
        self.logger.setLevel(self.previous_level)

    def _wait_for_sent(self, text, timeout=5):
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            if any(text in str(batch) for batch in self.gateway.sent):
                return True
            sleep(0.05)
        return False

    def test_oversized_message_is_dropped_and_following_messages_are_sent(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.logger.info("x" * 5000)
            self.logger.info("message after oversized one")
            delivered = self._wait_for_sent("message after oversized one")

        self.assertTrue(delivered)
        self.assertEqual(stdout.getvalue().count("Too big LOG message size"), 1)
        self.assertFalse(any("x" * 5000 in str(batch) for batch in self.gateway.sent))


class TestRemoteLoggingLevelIgnored(TestCase):
    def test_remote_logging_level_from_platform_is_not_applied(self):
        gateway = TBGatewayService.__new__(TBGatewayService)
        gateway.remote_handler = Mock(spec=TBRemoteLoggerHandler)

        with patch.object(service_module, 'log', Mock()) as log_mock:
            gateway._TBGatewayService__process_attribute_update({'RemoteLoggingLevel': 'DEBUG'})
            gateway._TBGatewayService__process_attributes_response({'RemoteLoggingLevel': 'DEBUG'}, {})

        gateway.remote_handler.activate_remote_logging_for_level.assert_not_called()
        warnings = [call.args[0] for call in log_mock.warning.call_args_list]
        self.assertEqual(sum("RemoteLoggingLevel" in message for message in warnings), 2)
