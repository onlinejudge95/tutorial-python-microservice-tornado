# Copyright (c) 2019. All rights reserved.

import time


def unixtime_now_millis() -> int:
    return int(time.time() * 1e3)
