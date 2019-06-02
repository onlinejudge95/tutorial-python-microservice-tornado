# Copyright (c) 2019. All rights reserved.

import logging
from typing import Dict

from addrservice import LOGGER_NAME
from addrservice.addressbook_db import (
    create_addressbook_db,
    AbstractAddressBookDB,
)
import addrservice.tracing as tracing
from addrservice.utils import unixtime_now_millis


class AddressBookService:
    def __init__(
        self,
        addr_db: AbstractAddressBookDB,
        logger: logging.Logger = logging.getLogger(LOGGER_NAME)
    ) -> None:
        self.start_time = unixtime_now_millis()
        self.addr_db = addr_db
        self.logger = logger

    @classmethod
    def from_config(cls, config: Dict):
        tracing.configure_tracing(config.get('tracing', {}))
        addr_db = create_addressbook_db(config['addr-db'])
        return cls(addr_db)

    def start(self):
        self.addr_db.start()

    def stop(self):
        self.addr_db.stop()
        tracing.trace_log(self.logger)

    def uptime_millis(self) -> int:
        return unixtime_now_millis() - self.start_time

    async def status(self):
        # In real world, it checks status of underlying resources (such as
        # database in this case) to set ready flag.
        return {
            'ready': True,
            'uptime': self.uptime_millis()
        }

    @tracing.trace()
    async def post_address(self, value: Dict) -> str:
        key = await self.addr_db.create_address(value)
        return key

    @tracing.trace()
    async def get_address(self, key: str) -> Dict:
        value = await self.addr_db.read_address(key)
        return value

    @tracing.trace()
    async def put_address(self, key: str, value: Dict) -> None:
        await self.addr_db.update_address(key, value)

    @tracing.trace()
    async def delete_address(self, key: str) -> None:
        await self.addr_db.delete_address(key)

    @tracing.trace()
    async def get_all_addresses(self) -> Dict[str, Dict]:
        values = await self.addr_db.read_all_addresses()
        return values
