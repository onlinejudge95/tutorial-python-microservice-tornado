# Copyright (c) 2019. All rights reserved.

import asynctest  # type: ignore
import unittest

from addrservice.addressbook_db import InMemoryAddressBookDB
from addrservice.service import AddressBookService
import addrservice.tracing as tracing

from tests.unit.address_data_test import address_data_suite


class AddressBookServiceWithInMemoryDBTest(asynctest.TestCase):
    async def setUp(self) -> None:
        self.addr_db = InMemoryAddressBookDB()
        tracing.set_trace_collectors([
            tracing.CummulativeFunctionTimeProfiler()
        ])
        self.service = AddressBookService(self.addr_db)
        self.service.start()

        self.address_data = address_data_suite()
        for nickname, addr in self.address_data.items():
            await self.addr_db.create_address(addr, nickname)

    async def tearDown(self) -> None:
        self.service.stop()

    def test_uptime(self) -> None:
        self.assertGreater(self.service.uptime_millis(), 0)

    @asynctest.fail_on(active_handles=True)
    async def test_status(self) -> None:
        status = await self.service.status()
        self.assertTrue(status['ready'])
        self.assertGreater(status['uptime'], 0)

    @asynctest.fail_on(active_handles=True)
    async def test_get_address(self) -> None:
        for nickname, addr in self.address_data.items():
            value = await self.service.get_address(nickname)
            self.assertEqual(addr, value)

    @asynctest.fail_on(active_handles=True)
    async def test_get_all_addresses(self) -> None:
        all_addr = await self.service.get_all_addresses()
        self.assertEqual(len(all_addr), 2)

    @asynctest.fail_on(active_handles=True)
    async def test_post_put_delete_address(self) -> None:
        nicknames = list(self.address_data.keys())
        self.assertGreaterEqual(len(nicknames), 2)

        addr0 = self.address_data[nicknames[0]]
        key = await self.service.post_address(addr0)
        val = await self.service.get_address(key)
        self.assertEqual(addr0, val)

        addr1 = self.address_data[nicknames[1]]
        await self.service.put_address(key, addr1)
        val = await self.service.get_address(key)
        self.assertEqual(addr1, val)

        await self.service.delete_address(key)

        with self.assertRaises(KeyError):
            await self.service.get_address(key)


if __name__ == '__main__':
    unittest.main()
