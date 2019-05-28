# Copyright (c) 2019. All rights reserved.

import asynctest  # type: ignore
from io import StringIO
from typing import Dict
import unittest
import yaml

from addrservice.addressbook_db import (
    create_addressbook_db, InMemoryAddressBookDB, SQLAddressBookDB
)

from tests.unit.address_data_test import address_data_suite


class AbstractAddressBookDBTest(unittest.TestCase):
    def read_config(self, txt: str) -> Dict:
        with StringIO(txt) as f:
            cfg = yaml.load(f.read(), Loader=yaml.SafeLoader)
        return cfg

    def test_in_memory_db_config(self):
        cfg = self.read_config('''
addr-db:
  memory: null
        ''')

        self.assertIn('memory', cfg['addr-db'])
        db = create_addressbook_db(cfg['addr-db'])
        self.assertEqual(type(db), InMemoryAddressBookDB)

    def test_sql_db_config(self):
        cfg = self.read_config('''
addr-db:
  sql:
    cred-file: /a/b/c.json
        ''')

        self.assertIn('sql', cfg['addr-db'])
        db = create_addressbook_db(cfg['addr-db'])
        self.assertEqual(type(db), SQLAddressBookDB)


class InMemoryAddressBookDBTest(asynctest.TestCase):
    def setUp(self) -> None:
        self.address_data = address_data_suite()
        self.addr_db = InMemoryAddressBookDB()

    @asynctest.fail_on(active_handles=True)
    async def test_crud_lifecycle(self) -> None:
        # Nothing in the database
        for nickname in self.address_data:
            with self.assertRaises(KeyError):
                await self.addr_db.read_address(nickname)

        # Create then Read, again Create(fail)
        for nickname, addr in self.address_data.items():
            await self.addr_db.create_address(addr, nickname)
            await self.addr_db.read_address(nickname)
            with self.assertRaises(KeyError):
                await self.addr_db.create_address(addr, nickname)

        self.assertEqual(len(self.addr_db.db), 2)

        # First data in test set
        first_nickname = list(self.address_data.keys())[0]
        first_addr = self.address_data[first_nickname]

        # Update
        await self.addr_db.update_address(first_nickname, first_addr)
        with self.assertRaises(ValueError):
            await self.addr_db.update_address(first_nickname, {})
        with self.assertRaises(KeyError):
            await self.addr_db.update_address('does not exist', first_addr)

        # Create without giving nickname
        new_nickname = await self.addr_db.create_address(addr)
        self.assertIsNotNone(new_nickname)
        self.assertEqual(len(self.addr_db.db), 3)

        # Get All Addresses
        addresses = await self.addr_db.read_all_addresses()
        self.assertEqual(len(addresses), 3)

        # Delete then Read, and the again Delete
        for nickname in self.address_data:
            await self.addr_db.delete_address(nickname)
            with self.assertRaises(KeyError):
                await self.addr_db.read_address(nickname)
            with self.assertRaises(KeyError):
                await self.addr_db.delete_address(nickname)

        self.assertEqual(len(self.addr_db.db), 1)

        await self.addr_db.delete_address(new_nickname)
        self.assertEqual(len(self.addr_db.db), 0)


async def mock_sql_execute_query(qyery: str) -> str:
    return '{}'


class SQLAddressBookDBTest(asynctest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.address_data = address_data_suite()
        self.addr_db = SQLAddressBookDB()

    @asynctest.fail_on(active_handles=True)
    @asynctest.patch('addrservice.addressbook_db.SomeSQLdbConnector.execute', side_effect=mock_sql_execute_query)  # noqa
    async def test_crud_functions(self, sql_execute_fn) -> None:
        nickname = list(self.address_data.keys())[0]
        addr = self.address_data[nickname]

        new_nickname = await self.addr_db.create_address(addr)
        await self.addr_db.read_address(new_nickname)
        await self.addr_db.update_address(new_nickname, addr)
        await self.addr_db.delete_address(new_nickname)

        self.assertEqual(sql_execute_fn.call_count, 4)

    @asynctest.fail_on(active_handles=True)
    async def test_read_all_addresses(self) -> None:
        # TODO: Exercise: implement this function and update mock/patch
        # annotations and # parameters of this function, and implement
        # suitable asserts to test SQLAddressBookDB.read_all_addresses
        pass


if __name__ == '__main__':
    unittest.main()
