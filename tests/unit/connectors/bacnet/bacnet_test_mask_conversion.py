import logging
from unittest import TestCase

from thingsboard_gateway.connectors.bacnet.bacnet_connector import AsyncBACnetConnector


class TestApplicationMaskValidation(TestCase):
    def setUp(self):
        self.bacnet_connector = AsyncBACnetConnector.__new__(AsyncBACnetConnector)
        self.bacnet_connector._AsyncBACnetConnector__log = logging.getLogger("bacnet mask tests")

        self.default_application_config = {
            "objectName": "TB_gateway123",
            "host": "192.168.1.136",
            "port": "47808",
            "mask": 22,
            "objectIdentifier": 594,
            "vendorIdentifier": 11,
            "maxApduLengthAccepted": 1476,
            "segmentationSupported": "noSegmentation",
            "networkNumber": 1,
            "deviceDiscoveryTimeoutInSec": 5,
        }

    def validate_mask(self, mask_to_test):
        connector_config = {"application": dict(self.default_application_config)}
        connector_config["application"]["mask"] = mask_to_test
        self.bacnet_connector._AsyncBACnetConnector__config = connector_config

        is_valid = self.bacnet_connector._AsyncBACnetConnector__is_valid_application_device_section()
        normalized_app_config = self.bacnet_connector._AsyncBACnetConnector__config["application"]
        return is_valid, normalized_app_config

    def test_accepts_integer_cidr_prefixes_0_to_32(self):
        for cidr_prefix in range(0, 33):
            with self.subTest(cidr_prefix=cidr_prefix):
                is_valid, app_config = self.validate_mask(cidr_prefix)
                self.assertTrue(is_valid)
                self.assertEqual(app_config["mask"], cidr_prefix)

    def test_out_of_range_integer_masks_fall_back_to_default_24(self):
        for invalid_prefix in [33, 100, 999999, -1]:
            with self.subTest(invalid_prefix=invalid_prefix):
                is_valid, app_config = self.validate_mask(invalid_prefix)
                self.assertTrue(is_valid)
                self.assertEqual(app_config["mask"], 24)

    def test_non_integer_masks_fall_back_to_default_24(self):
        for invalid_mask in ["24", "255.255.255.0", "abc", "", None]:
            with self.subTest(invalid_mask=invalid_mask):
                is_valid, app_config = self.validate_mask(invalid_mask)
                self.assertTrue(is_valid)
                self.assertEqual(app_config["mask"], 24)
