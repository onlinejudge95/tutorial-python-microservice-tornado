# Copyright (c) 2019. All rights reserved.

import glob
import json
import jsonschema  # type: ignore
import os
from typing import Dict, List
import unittest

from addrservice import ADDRESS_BOOK_SCHEMA, ADDR_SERVICE_ROOT_DIR

ADDRESS_DATA_DIR = os.path.abspath(os.path.join(
    ADDR_SERVICE_ROOT_DIR,
    '../tests/data/addresses'
))

ADDRESS_FILES = glob.glob(ADDRESS_DATA_DIR + '/*.json')


def address_data_suite(
    json_files: List[str] = ADDRESS_FILES
) -> Dict[str, Dict]:
    addr_data_suite = {}

    for fname in json_files:
        nickname = os.path.splitext(os.path.basename(fname))[0]
        with open(fname, mode='r', encoding='utf-8') as f:
            addr_json = json.load(f)
            addr_data_suite[nickname] = addr_json

    return addr_data_suite


class AddressJsonDataTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.address_data = address_data_suite()

    def test_json_schema(self) -> None:
        # Validate Address Schema
        jsonschema.Draft7Validator.check_schema(ADDRESS_BOOK_SCHEMA)

    def test_address_data_json(self) -> None:
        # Validate Address Test Data
        for nickname, addr in self.address_data.items():
            # validate using application subschema
            jsonschema.validate(addr, ADDRESS_BOOK_SCHEMA)


if __name__ == '__main__':
    unittest.main()
