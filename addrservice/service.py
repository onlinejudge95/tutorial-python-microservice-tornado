# Copyright (c) 2019. All rights reserved.

from typing import Dict

from addrservice.addressbook_db import AbstractAddressBookDB
from addrservice.utils import unixtime_now_millis


class AddressBookService:
    def __init__(self, addr_db: AbstractAddressBookDB) -> None:
        self.start_time = unixtime_now_millis()
        self.addr_db = addr_db

    def start(self):
        self.addr_db.start()

    def stop(self):
        self.addr_db.stop()

    def uptime_millis(self) -> int:
        return unixtime_now_millis() - self.start_time

    async def status(self):
        # In real world, it checks status of underlying resources (such as
        # database in this case) to set ready flag.
        return {
            'ready': True,
            'uptime': self.uptime_millis()
        }

    async def post_address(self, value: Dict) -> str:
        key = await self.addr_db.create_address(value)
        return key

    async def get_address(self, key: str) -> Dict:
        value = await self.addr_db.read_address(key)
        return value

    async def put_address(self, key: str, value: Dict) -> None:
        await self.addr_db.update_address(key, value)

    async def delete_address(self, key: str) -> None:
        await self.addr_db.delete_address(key)

    async def get_all_addresses(self) -> Dict[str, Dict]:
        values = await self.addr_db.read_all_addresses()
        return values
