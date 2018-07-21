#!/usr/bin/python3

import unittest
from servicecom import Wifi

class Test(unittest.TestCase):

    def test_create(self):
        Wifi.network_props()

    def test_disconnect(self):
        Wifi.disconnect()

    def test_reconnect(self):
        Wifi.reconnect()

    def verify_test(self):
        Wifi.verify()

    def test_connection_test(self):
        Wifi.test_connection()


if __name__ == '__main__':
    unittest.main()
