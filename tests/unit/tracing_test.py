# Copyright (c) 2019. All rights reserved.

import unittest

from addrservice.tracing import (
    set_trace_collectors,
    trace,
    CummulativeFunctionTimeProfiler,
    Timeline
)


class TraceTest(unittest.TestCase):
    def test_trace_decorator(self):
        profiler = CummulativeFunctionTimeProfiler()
        timeline = Timeline()
        set_trace_collectors([profiler, timeline])

        @trace()
        def factorial(n: int) -> int:
            if n < 0:
                raise ValueError('n={} should be greater than 0'.format(n))
            return 1 if n <= 1 else n * factorial(n-1)

        self.assertEqual(factorial.__name__, 'factorial')

        with self.assertRaises(ValueError):
            factorial(-1)

        fact = factorial(5)
        self.assertEqual(fact, 120)

        factorial_qualname = 'TraceTest.test_trace_decorator.<locals>.factorial'  # noqa
        profiler_summary = profiler.summary()
        self.assertEqual(str(profiler), str(profiler_summary))

        self.assertEqual(len(profiler_summary), 1)
        self.assertEqual(profiler_summary[0][0], factorial_qualname)
        self.assertGreater(profiler_summary[0][1], 0)

        self.assertEqual(len(timeline.timeline), 1*2 + 5*2)
        self.assertEqual(str(timeline), str(timeline.timeline))

        set_trace_collectors([])


if __name__ == '__main__':
    unittest.main()
