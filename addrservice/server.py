# Copyright (c) 2019. All rights reserved.

import argparse
import asyncio
import signal
from typing import Dict
import yaml

import tornado.platform.asyncio as tasyncio
import tornado.web

from addrservice.addressbook_db import create_addressbook_db
from addrservice.app import make_addrservice_app
from addrservice.service import AddressBookService


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Run Address Book Server'
    )

    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=8080,
        help='port number for %(prog)s server to listen; '
        'default: %(default)s'
    )

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='turn on debug logging'
    )

    parser.add_argument(
        '-c',
        '--config',
        required=True,
        type=argparse.FileType('r'),
        help='config file for %(prog)s'
    )

    args = parser.parse_args(args)
    return args


def run_server(
    app: tornado.web.Application,
    service: AddressBookService,
    config: Dict,
    port: int,
    debug: bool,
):
    name = config['service']['name']

    # Install async IO event loop instead of Tornado's IO loop for standard
    # async/await code and Tornado to work in same even loop.
    tasyncio.AsyncIOMainLoop().install()

    # Register loop.stop() as signal handler
    # In 3.6, shutting down gracefully is a lot simpler, so when we move
    # try:
    #     loop.run_forever()
    # finally:
    #     loop.run_until_complete(loop.shutdown_asyncgens())
    #     loop.close()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

    # Start auth, caller's start_up and server
    service.start()

    # Start http server
    http_server_args = {
        'decompress_request': True
    }

    http_server = app.listen(port, '', **http_server_args)
    msg = 'Starting {} on port {} ...'.format(name, port)
    print(msg)

    # Start event loop
    # asyncio equivalent of tornado.ioloop.IOLoop.current().start()
    loop.run_forever()

    # Begin shutdown after loop.stop() upon receiving signal
    msg = 'Shutting down {}...'.format(name)
    print(msg)

    http_server.stop()
    # Run unfinished tasks and stop event loop
    loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
    service.stop()
    loop.close()

    # Service stopped
    msg = 'Stopped {}.'.format(name)
    print(msg)


def main(args=parse_args()):
    '''
    Starts the Tornado server serving Address Book on the given port
    '''

    config = yaml.load(args.config.read(), Loader=yaml.SafeLoader)
    addr_db = create_addressbook_db(config['addr-db'])
    addr_service = AddressBookService(addr_db)
    addr_app = make_addrservice_app(addr_service, config, args.debug)

    run_server(
        app=addr_app,
        service=addr_service,
        config=config,
        port=args.port,
        debug=args.debug,
    )


if __name__ == '__main__':
    main()
