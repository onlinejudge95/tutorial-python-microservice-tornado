# Copyright (c) 2019. All rights reserved.

from abc import ABCMeta, abstractmethod
import json
import jsonschema  # type: ignore
from typing import Any, Dict
import uuid

from addrservice import ADDRESS_BOOK_SCHEMA


class AbstractAddressBookDB(metaclass=ABCMeta):
    def start(self):
        pass

    def stop(self):
        pass

    def validate_address(self, addr: Dict) -> None:
        try:
            jsonschema.validate(addr, ADDRESS_BOOK_SCHEMA)
        except jsonschema.exceptions.ValidationError:
            raise ValueError('JSON Schema validation failed')

    # CRUD

    @abstractmethod
    async def create_address(self, addr: Dict, nickname: str = None) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def read_address(self, nickname: str) -> Dict:
        raise NotImplementedError()

    @abstractmethod
    async def update_address(self, nickname: str, addr: Dict) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete_address(self, nickname: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def read_all_addresses(self) -> Dict[str, Dict]:
        raise NotImplementedError()


class InMemoryAddressBookDB(AbstractAddressBookDB):
    def __init__(self):
        self.db = {}

    async def create_address(self, addr: Dict, nickname: str = None) -> str:
        if nickname is None:
            nickname = uuid.uuid4().hex

        if nickname in self.db:
            raise KeyError('{} already exists'.format(nickname))

        self.validate_address(addr)

        self.db[nickname] = addr
        return nickname

    async def read_address(self, nickname: str) -> Dict:
        return self.db[nickname]

    async def update_address(self, nickname: str, addr: Dict) -> None:
        if nickname is None or nickname not in self.db:
            raise KeyError('{} does not exist'.format(nickname))

        self.validate_address(addr)

        self.db[nickname] = addr

    async def delete_address(self, nickname: str) -> None:
        if nickname is None or nickname not in self.db:
            raise KeyError('{} does not exist'.format(nickname))

        del self.db[nickname]

    async def read_all_addresses(self) -> Dict[str, Dict]:
        return self.db


class SomeSQLdbConnector:
    '''
    For sake of simplicity in this tutorial, and avoiding complexity of
    credentials etc., this class provides a typical remote DB query connector
    interface. In real world, asyncpg or MySQLdb cursor packages will be used.

    Use here is limited in scope to demo how to mock such calls.
    '''

    async def execute(self, query: str) -> Any:
        raise NotImplementedError()


class SQLAddressBookDB(AbstractAddressBookDB):
    def __init__(self):
        self.db_connector = SomeSQLdbConnector()

    async def create_address(self, addr: Dict, nickname: str = None) -> str:
        if nickname is None:
            nickname = uuid.uuid4().hex

        self.validate_address(addr)

        query = '''INSERT INTO
                   ADDRESSES (NICKNAME, ADDRESS)
                   VALUES ('{}' ,'{}')
                '''.format(nickname, json.dumps(addr))
        await self.db_connector.execute(query)
        return nickname

    async def read_address(self, nickname: str) -> Dict:
        query = '''SELECT * FROM ADDRESSES
                   WHERE NICKNAME = '{}'
                '''.format(nickname)
        addr_json_str = await self.db_connector.execute(query)

        return json.loads(addr_json_str)

    async def update_address(self, nickname: str, addr: Dict) -> None:
        self.validate_address(addr)

        query = '''UPDATE ADDRESSES
                   SET ADDRESS = '{}'
                   WHERE NICKNAME = '{}'
                '''.format(json.dumps(addr), nickname)
        await self.db_connector.execute(query)

    async def delete_address(self, nickname: str) -> None:
        query = ''' DELETE FROM ADDRESS
                   WHERE NICKNAME = '{}'
                '''.format(nickname)
        await self.db_connector.execute(query)

    async def read_all_addresses(self) -> Dict[str, Dict]:
        # TODO: Exercise: implement suitable query/abstraction and update
        # the SQLAddressBookDBTest.test_read_all_addresses to test this.
        raise NotImplementedError()


def create_addressbook_db(addr_db_config: Dict) -> AbstractAddressBookDB:
    db_type = list(addr_db_config.keys())[0]
    db_config = addr_db_config[db_type]

    return {
        'memory': lambda cfg: InMemoryAddressBookDB(),
        'sql': lambda cfg: SQLAddressBookDB()
    }[db_type](db_config)
