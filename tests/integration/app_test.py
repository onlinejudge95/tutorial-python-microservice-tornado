# Copyright (c) 2019. All rights reserved.

import atexit
from io import StringIO
import json
import unittest
import yaml

from tornado.ioloop import IOLoop
import tornado.testing

from addrservice.addressbook_db import create_addressbook_db
from addrservice.service import AddressBookService
from addrservice.app import make_addrservice_app


IN_MEMORY_CFG_TXT = '''
service:
  name: Address Book Test

addr-db:
  memory: null
'''

with StringIO(IN_MEMORY_CFG_TXT) as f:
    TEST_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)


class TestAddressServiceApp(tornado.testing.AsyncHTTPTestCase):
    def get_app(self) -> tornado.web.Application:
        # get_app is the hook that Tornado Test uses to get app under test
        addr_db = create_addressbook_db(TEST_CONFIG['addr-db'])
        addr_service = AddressBookService(addr_db)

        addr_service.start()
        atexit.register(lambda: addr_service.stop())

        return make_addrservice_app(
            service=addr_service,
            config=TEST_CONFIG,
            debug=True
        )

    def get_new_ioloop(self):
        IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
        instance = IOLoop.instance()
        return instance

    def test_liveness(self):
        r = self.fetch(
            '/healthz',
            method='GET',
            headers=None,
        )
        info = json.loads(r.body.decode('utf-8'))

        self.assertEqual(r.code, 200, info)
        self.assertGreater(info['uptime'], 0)

    def test_readiness(self):
        r = self.fetch(
            '/readiness',
            method='GET',
            headers=None,
        )
        info = json.loads(r.body.decode('utf-8'))

        self.assertEqual(r.code, 200, info)
        self.assertTrue(info['ready'])
        self.assertGreater(info['uptime'], 0)

    def test_default_handler(self):
        r = self.fetch(
            '/does-not-exist',
            method='GET',
            headers=None,
        )
        # info = json.loads(r.body.decode('utf-8'))

        # TODO: Exercise: Tornado, by default, send HTML response on 404.
        # Implement BaseRequestHandler.write_error method to return a JSON
        # response, and hook DefaultRequestHandler to tornado.web.Application
        # creation with suitable args so that the last two assert statements
        # of this test function start passing.
        info = r.body
        # print(info)

        self.assertEqual(r.code, 404, info)
        # self.assertEqual(info['code'], 404)
        # self.assertEqual(info['message'], 'Unknown Endpoint')


if __name__ == '__main__':
    unittest.main()
