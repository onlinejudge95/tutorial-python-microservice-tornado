# Tutorial: Building, testing and profiling efficient micro-services using Tornado

## Pre-req: Environment Setup and Sanity Test

Get the source code for tutorial:
```
$ git clone git@github.com:scgupta/tutorial-python-microservice-tornado.git
```

Need Create and activate Vitual Environment:
```
$ python3 -m venv env
$ source env/bin/activate
$ pip install --upgrade pip
$ pip3 install -r ./requirements.txt
```

Verify that the source code and environment is setup correctly, first run the tests:
```
$ pwd
.../turorial-python-microservice-tornado
$ python3 ./run.py test
```

Now start the server manually:
```
$ python3 ./addrservice/server.py --debug --port 8080 --config ./configs/addressbook-local.yaml
```

In another terminal, watch the log file:
```
$ tail -f tail -f /tmp/addrservice-app.log
```

Now send a request to the server using Postman or curl to check if it is responding:
```
$ curl http://localhost:8080/healthz
{"uptime": <some number>}
$ curl http://localhost:8080/readiness
{"ready": true, "uptime": <some number>}
$ curl http://localhost:8080/addressbook
{}
```

If you get these responses, you are all set for the tutorial.

## Data Model and Test Data

This simple example micro-service servers an address book, The JSON schema for the data model is in `addrservice/address-book-v1.0.json`, and test data in `tests/data/addresses`.

Run unit tests to check any error in the JSON schema or test data:
```
$ pwd
.../turorial-python-microservice-tornado
$ python -m unittest discover tests -p '*_test.py'
```

That commonad to run unit tests is quite mouthful, so a run utility is included:
```
$ ./run.py test
```

The `run.py` script also has options to run linter and static type checker too. For example, run `flake8` by either of the following command:
```
$ flake8 addrservice tests
$ ./run.py lint
```
And, run `mypy` by either of the following:
```
$ mypy addrservice tests
$ ./run.py typecheck
```

## Unit Tests, Mocking, Code Coverage

Take a look at the `AbstractAddressBookDB` in `addrservice/addressbook_db.py`. It implents a simple abstraction of CRUD fuctions for address book. Notice that all CRUD functions are `async`, i.e. the caller must `await` on them.

`InMemoryAddressBookDB` is an in-memory DB implementation of this abstraction. Such implementation comes handy to run and debug unit tests.

In real world, the DB is a remote data store like MySQL, PostgreSQL, MongoDB etc., or some key-value or graph store depending on the need. Setting up and using such remote data store is outside the scope of this tutorial. But to demonstrate how to mock _only_ the calls to database connecter, `SQLAddressBookDB` is a limited implementation of `AbstractAddressBookDB`. It assumes that any SQL DB connector will have function to execute queries, which unit tests must mock.

The unit tests for these are in `tests/unit/addressbook_db_test.py`, which can be run with `run.py`:
```
$ ./run.py test
```

Next step is to check the code coverage:
```
$ coverage run --source=addrservice --branch ./run.py test
$ coverage report
Name                            Stmts   Miss Branch BrPart  Cover
-----------------------------------------------------------------
addrservice/__init__.py             6      0      0      0   100%
addrservice/addressbook_db.py      79      9     10      1    89%
-----------------------------------------------------------------
TOTAL                              85      9     10      1    89%
```

To see coverage reports in HTML:
```
$ coverage html
$ open htmlcov/index.html
```

Click on the link to coverage report for `addrservice/addressbook_db.py`, and examine lines that are not covered.

### Exercise

Implement `SQLAddressBookDB.get_all_addresses()` function in `addrservice/addressbook_db.py` and its test in `tests/unit/addressbook_db_test.py`. Generate and examine the code coverage report.

**Bonus Problem:** Hook `SQLAddressBookDB` to `asyncpg` or any other SQL DB connector.


## Microservice

File `addrservice/servive.py` has REST microservice post, get, put, delete functions for address. This file is indpendent of any web service framework. While it appears simple because there is only one data store, but in reality a service can interact with multiple data sources and other services (such as auth). Defining a service interface without mixing nitty-gritty of a web service framework not just prevents perculation of chosen framework dependencies across the system, but also this layered approach makes it easy to isolate bugs.

Having an in-memory database facilates better integration testing because asserts can test the state of the database. Integration tests for service are in `tests/integration/addressservice_test.py`.

[Tornado](https://www.tornadoweb.org/) is a framework to develop Python web/microservices. It uses async effectively to achieve high number of open connections. In this tutorial, we create a `tornado.web.Application` and add `tornado.web.RequestHandlers` in file `addrservice/app.py` to serve various API endpoints for this address service. Tornado also has a rich framework for testing.

Web services return HTML back. In address book microservice, API data interface is JSON. We will examine key Tornado APIs of `Application`, `RequestHandler` and `tornado.testing` to develop it.

But first, let's run the server and test it:

```
$ python3 addrservice/server.py --config ./configs/addressbook-local.yaml --debug
Starting Address Book on port 8080 ...

```

Test the health and readiness endpoints (needed in most cloud service orchestrators like Kubernetes):

`GET /health`:
```
$ curl -X 'GET' http://localhost:8080/healthz
{"uptime": 184852}
``` 

`GET /readiness`:
```
$ curl -X 'GET' http://localhost:8080/readiness
{"ready": true, "uptime": 292907}
```

Also run lint, typecheck and test to verify nothing is broken, and also code coverage:
```
$ ./run.py lint
$ ./run.py typecheck
$ ./run.py test -v
$ coverage run --source=addrservice --branch ./run.py test
$ coverage report
Name                            Stmts   Miss Branch BrPart  Cover
-----------------------------------------------------------------
addrservice/__init__.py             6      0      0      0   100%
addrservice/addressbook_db.py      85      7     13      1    92%
addrservice/app.py                 28      3      0      0    89%
addrservice/server.py              45     45      4      0     0%
addrservice/service.py             28      0      0      0   100%
addrservice/utils.py                3      0      0      0   100%
-----------------------------------------------------------------
TOTAL                             195     55     17      1    72%
```

You might notice that there is no code coverage of `addrservice/server.py`, this is the file used to start the server. Since Torando test framework has a mechanism to start the server in the same process where tests are running, this file does not get tested by unit and integration tests. Coverage of `addrservice/app.py` will improve as you finish exercises.

Now since all the plumbing is working, let's add addressbook API endpoints through two Request Handlers:

`AddressBookRequestHandler`:

- `GET /addressbook`: gets all addresses in the address book
- `POST /addressbook`: create an entry in the addressbook

`AddressBookEntryRequestHandler`:

- `GET /addressbook/<id>`: get the address book entry with given id
- `PUT /addressbook/<id>`: update the address book entry with given id
- `DELETE /addressbook/<id>`: delete the address book entry with given id

Here is a sample session exercising all endpoints (notice the POST response has Location in the Headers containing the URI/id `d2fbda62ee274243a3c06bc39c7a8b22` of the entry that gets created):
```
$ curl -X 'GET' http://localhost:8080/addressbook
{}

$ curl -i -X 'POST' -H "Content-Type: application/json" -d "@tests/data/addresses/namo.json" http://localhost:8080/addressbook
HTTP/1.1 100 (Continue)
HTTP/1.1 201 Created
Server: TornadoServer/6.0.2
Content-Type: text/html; charset=UTF-8
Location: /addressbook/d2fbda62ee274243a3c06bc39c7a8b22
Content-Length: 0

$ curl -X 'GET' http://localhost:8080/addressbook/d2fbda62ee274243a3c06bc39c7a8b22
{"name": "Narendra Modi", ...}

$ curl -X 'GET' http://localhost:8080/addressbook
{"d2fbda62ee274243a3c06bc39c7a8b22": {"name": "Narendra Modi", ...}

$ curl -i -X 'PUT' -H "Content-Type: application/json" -d "@tests/data/addresses/raga.json" http://localhost:8080/addressbook/d2fbda62ee274243a3c06bc39c7a8b22
HTTP/1.1 100 (Continue)
HTTP/1.1 204 No Content
Server: TornadoServer/6.0.2

$ curl -X 'GET' http://localhost:8080/addressbook/d2fbda62ee274243a3c06bc39c7a8b22
{"name": "Rahul Gandhi", ...}

$ curl -i -X 'DELETE' http://localhost:8080/addressbook/d2fbda62ee274243a3c06bc39c7a8b22
HTTP/1.1 204 No Content
Server: TornadoServer/6.0.2

$ curl -X 'GET' http://localhost:8080/addressbook
{}
```

## Logging

Logging are useful in diagnosing services, more so when async is involved. Python has a standard [logging](https://docs.python.org/3/library/logging.html) package, and its documentation includes an excellent [HOWTO](https://docs.python.org/3/howto/logging.html) guide and [Cookbook](https://docs.python.org/3/howto/logging-cookbook.html). These are rich source of information, and leave nothoing much to add. Following are some of the best practices in my opinion:

- Do NOT use ROOT logger directly throgh `logging.debug()`, `logging.error()` methods directly because it is easy to overlook their default behavior.
- Do NOT use module level loggers of variety `logging.getLogger(__name__)` because any complex project will require controlling logging through configuration (see next point). These may cause surprise if you forget to set `disable_existing_loggers` to false or overlook how modules are loaded and initialized. If use at all, call `logging.getLogger(__name__)` inside function, rather than outside at the beginning of a module.
- `dictConfig` (in `yaml`) offers right balance of versatility and flexibility compared to `ini` based `fileConfig`or doing it in code. Specifying logger in config files allows you to use different logging levels and infra in prod deployment, stage deployments, and local debugging (with increasingly more logs).

Here is a part of `configs/addressbook-local.yaml` using [logging.config](https://docs.python.org/3/library/logging.config.html) syntax:
```
version: 1
formatters:
  brief:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d %(funcName)s() - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: brief
    stream: ext://sys.stdout
  file:
    class : logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: /tmp/addrservice-app.log
    backupCount: 3
loggers:
  addrservice:
    level: DEBUG
    handlers:
      - console
      - file
    propagate: no
  tornado.general:
    level: DEBUG
    handlers:
      - file
root:
  level: WARNING
  handlers:
    - console
```

Notice that this configuration not just defines a logger `addrservice` for this service, but also modifies behavior of Tornado's general logger. There are several pre-defined [handlers](https://docs.python.org/3/library/logging.handlers.html). Here the SteamHandler and RotatingFileHandler are being used to write to console and log files respectively.


## Tracing

Tracing is implemented throgh a decorator and a bunch of trace data collectors that can be specified in the config.
