# Copyright (c) 2019. All rights reserved.

from typing import (
    Any,
    Awaitable,
    Dict,
    Optional,
)

import tornado.web

from addrservice.service import AddressBookService


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
            # TODO: implement following endpoints
            # GET /addresses/
            # POST /addresses/
            # GET /addresses/<id>
            # PUT /addresses/<id>
            # DELETE /addresses/<id>
        ],
        serve_traceback=debug,  # it is passed on as setting to write_error()
        # TODO: Exercise: add here suitable values for default_handler_class
        # and default_handler_args parameters to hook in DefaultRequestHandler
    )
