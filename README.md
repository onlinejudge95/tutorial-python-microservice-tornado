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
