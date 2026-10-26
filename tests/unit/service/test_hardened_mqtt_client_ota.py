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

from unittest import TestCase
from unittest.mock import Mock, patch

from simplejson import dumps
from tb_gateway_mqtt import TBGatewayMqttClient

from thingsboard_gateway.gateway.tb_client import HardenedTBGatewayMqttClient

FULL_FW_ATTRIBUTES = {
    "fw_title": "/thingsboard_gateway/extensions/evil.py",
    "fw_version": "2.0",
    "fw_size": 5,
    "fw_checksum": "abc",
    "fw_checksum_algorithm": "SHA256",
}


def _message(topic, payload):
    message = Mock()
    message.topic = topic
    message.payload = dumps(payload).encode()
    return message


class TestHardenedGatewayMqttClientOta(TestCase):
    def _create_client(self, client_class):
        client = client_class("localhost", 1883, "token")
        self.addCleanup(setattr, client, "stopped", True)
        client._TBDeviceMqttClient__is_connected = True
        client._client.publish = Mock(return_value=Mock(rc=0, mid=1))
        return client

    @staticmethod
    def _published_topics(client):
        return [call.kwargs.get("topic", call.args[0] if call.args else None)
                for call in client._client.publish.call_args_list]

    def test_library_client_starts_ota_download(self):
        # Guard: if the library stops reacting to fw_* attributes, the tests below become meaningless.
        client = self._create_client(TBGatewayMqttClient)
        with patch("tb_device_mqtt.sleep"):
            client._on_message(None, None, _message("v1/devices/me/attributes", FULL_FW_ATTRIBUTES))

        self.assertTrue(any(topic.startswith("v2/fw/request/") for topic in self._published_topics(client)))

    def test_fw_attribute_update_does_not_start_ota_download(self):
        client = self._create_client(HardenedTBGatewayMqttClient)
        callback = Mock()
        client.subscribe_to_all_attributes(callback)

        with patch("tb_device_mqtt.sleep") as sleep_mock:
            client._on_message(None, None, _message("v1/devices/me/attributes", FULL_FW_ATTRIBUTES))

        self.assertEqual(self._published_topics(client), [])
        sleep_mock.assert_not_called()
        callback.assert_called_once_with(FULL_FW_ATTRIBUTES, None)

    def test_incomplete_fw_attributes_do_not_raise(self):
        client = self._create_client(HardenedTBGatewayMqttClient)

        with patch("tb_device_mqtt.sleep"):
            client._on_message(None, None, _message("v1/devices/me/attributes", {"fw_version": "1.0"}))

        self.assertEqual(self._published_topics(client), [])

    def test_fw_attributes_in_attribute_response_do_not_start_ota_download(self):
        client = self._create_client(HardenedTBGatewayMqttClient)

        with patch("tb_device_mqtt.sleep"):
            client._on_message(None, None, _message("v1/devices/me/attributes/response/1",
                                                    {"shared": FULL_FW_ATTRIBUTES}))

        self.assertEqual(self._published_topics(client), [])
        self.assertFalse(client.firmware_received)
