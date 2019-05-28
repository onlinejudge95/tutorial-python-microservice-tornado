# Tutorial: Building, testing and profiling efficient micro-services using Tornado

## Environment Setup

Get the source code for tutorial:
```
$ git clone git@github.com:scgupta/turorial-python-microservice-tornado.git
```

Create and activate Vitual Environment:
```
$ python3 -m venv env
$ source env/bin/activate
$ pip install --upgrade pip
$ pip3 install -r ./requirements.txt
```

## Data Model and Test Data

This simple example micro-service servers an address book, The JSON schema for the data model is in `addrservice/address-book-v1.0.json`, and test data in `tests/data/addresses`.

Run unit tests to check any error in the JSON schema or test data:
```
$ pwd
.../turorial-python-microservice-tornado
$ python -m unittest discover tests -p '*_test.py'
```

That commonad to run unit tests is quite mouthful, so a run utility in included:
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
