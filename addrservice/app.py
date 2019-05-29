# Copyright (c) 2019. All rights reserved.

import json
from typing import (
    Any,
    Awaitable,
    Dict,
    Optional,
)

import tornado.web

from addrservice.service import AddressBookService

ADDRESSBOOK_REGEX = r'/addressbook/?'
ADDRESSBOOK_ENTRY_REGEX = r'/addressbook/(?P<id>[a-zA-Z0-9-]+)/?'
ADDRESSBOOK_ENTRY_URI_FORMAT_STR = r'/addressbook/{id}'


class BaseRequestHandler(tornado.web.RequestHandler):
    def initialize(self, service: AddressBookService, config: Dict) -> None:
        self.service = service
        self.config = config

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        super()
        # TODO: Exercise: Implement it to return JSON instead of Tornado's
        # default HTML implementation. Also, it should include stack trace
        # When debug is set to True in make_addrservice_app


class DefaultRequestHandler(BaseRequestHandler):
    def initialize(self, status_code, message):
        self.set_status(status_code, reason=message)

    def prepare(self) -> Optional[Awaitable[None]]:
        raise tornado.web.HTTPError(
            self._status_code, reason=self._reason
        )


class LivenessRequestHandler(BaseRequestHandler):
    async def get(self):
        status = 200
        info = dict(uptime=self.service.uptime_millis())
        self.set_status(status)
        self.finish(info)


class ReadinessRequestHandler(BaseRequestHandler):
    async def get(self):
        info = await self.service.status()
        status = 200 if info['ready'] else 503
        self.set_status(status)
        self.finish(info)


class AddressBookRequestHandler(BaseRequestHandler):
    async def get(self):
        all_addrs = await self.service.get_all_addresses()
        self.set_status(200)
        self.finish(all_addrs)

    async def post(self):
        try:
            addr = json.loads(self.request.body.decode('utf-8'))
            id = await self.service.post_address(addr)
            addr_uri = ADDRESSBOOK_ENTRY_URI_FORMAT_STR.format(id=id)
            self.set_status(201)
            self.set_header('Location', addr_uri)
            self.finish()
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(400, reason='Invalid JSON body')
        except ValueError as e:
            raise tornado.web.HTTPError(400, reason=str(e))


class AddressBookEntryRequestHandler(BaseRequestHandler):
    async def get(self, id):
        try:
            addr = await self.service.get_address(id)
            self.set_status(200)
            self.finish(addr)
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))

    async def put(self, id):
        # TODO: Exercise: implement this method. Remove 'no_' from
        # the 'no_test_address_book_endpoints' function in file
        # 'tests/integration/app_test.py', and all tests should pass.
        pass

    async def delete(self, id):
        try:
            await self.service.delete_address(id)
            self.set_status(204)
            self.finish()
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))


def make_addrservice_app(
    service: AddressBookService,
    config: Dict,
    debug: bool
) -> tornado.web.Application:
    return tornado.web.Application(
        [
            # Heartbeat
            (r'/healthz/?', LivenessRequestHandler, dict(service=service, config=config)),  # noqa
            (r'/readiness/?', ReadinessRequestHandler, dict(service=service, config=config)),  # noqa
            # Address Book endpoints
            (ADDRESSBOOK_REGEX, AddressBookRequestHandler, dict(service=service, config=config)),  # noqa
            (ADDRESSBOOK_ENTRY_REGEX, AddressBookEntryRequestHandler, dict(service=service, config=config))  # noqa
        ],
        serve_traceback=debug,  # it is passed on as setting to write_error()
        # TODO: Exercise: add here suitable values for default_handler_class
        # and default_handler_args parameters to hook in DefaultRequestHandler
    )
