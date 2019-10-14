# Copyright (c) 2019. All rights reserved.

import json
import logging
from typing import (
    Any,
    Awaitable,
    Dict,
    Optional,
    Tuple,
)

import tornado.web

from addrservice import LOGGER_NAME
from addrservice.service import AddressBookService

ADDRESSBOOK_REGEX = r'/addressbook/?'
ADDRESSBOOK_ENTRY_REGEX = r'/addressbook/(?P<id>[a-zA-Z0-9-]+)/?'
ADDRESSBOOK_ENTRY_URI_FORMAT_STR = r'/addressbook/{id}'


class BaseRequestHandler(tornado.web.RequestHandler):
    def initialize(
        self,
        service: AddressBookService,
        config: Dict,
        logger: logging.Logger
    ) -> None:
        self.service = service
        self.config = config
        self.logger = logger

    def prepare(self) -> Optional[Awaitable[None]]:
        msg = 'REQUEST: {method} {uri} ({ip})'.format(
            method=self.request.method,
            uri=self.request.uri,
            ip=self.request.remote_ip
        )
        self.logger.debug(msg)

        return super().prepare()

    def on_finish(self) -> None:
        super().on_finish()

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
        ) from None


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
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            ) from None
        except ValueError as e:
            raise tornado.web.HTTPError(400, reason=str(e)) from None


class AddressBookEntryRequestHandler(BaseRequestHandler):
    async def get(self, id):
        try:
            addr = await self.service.get_address(id)
            self.set_status(200)
            self.finish(addr)
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e)) from None

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
            raise tornado.web.HTTPError(404, reason=str(e)) from None


def log_function(handler: tornado.web.RequestHandler) -> None:
    status = handler.get_status()
    request_time = 1000.0 * handler.request.request_time()

    msg = 'RESPOSE: {status} {method} {uri} ({ip}) {time}ms'.format(
        status=status,
        method=handler.request.method,
        uri=handler.request.uri,
        ip=handler.request.remote_ip,
        time=request_time,
    )

    logger = getattr(handler, 'logger', logging.getLogger(LOGGER_NAME))

    if handler.get_status() < 400:
        logger.info(msg)
    elif handler.get_status() < 500:
        logger.warning(msg)
    else:
        logger.error(msg)


def make_addrservice_app(
    config: Dict,
    debug: bool,
    logger: logging.Logger = logging.getLogger(LOGGER_NAME)
) -> Tuple[AddressBookService, tornado.web.Application]:
    service = AddressBookService.from_config(config)

    app = tornado.web.Application(
        [
            # Heartbeat
            (r'/healthz/?', LivenessRequestHandler, dict(service=service, config=config, logger=logger)),  # noqa
            (r'/readiness/?', ReadinessRequestHandler, dict(service=service, config=config, logger=logger)),  # noqa
            # Address Book endpoints
            (ADDRESSBOOK_REGEX, AddressBookRequestHandler, dict(service=service, config=config, logger=logger)),  # noqa
            (ADDRESSBOOK_ENTRY_REGEX, AddressBookEntryRequestHandler, dict(service=service, config=config, logger=logger))  # noqa
        ],
        compress_response=True,  # compress textual responses
        log_function=log_function,  # log_request() uses it to log results
        serve_traceback=debug,  # it is passed on as setting to write_error()
        # TODO: Exercise: add here suitable values for default_handler_class
        # and default_handler_args parameters to hook in DefaultRequestHandler
    )

    return service, app
