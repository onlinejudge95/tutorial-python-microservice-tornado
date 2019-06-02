# Copyright (c) 2019. All rights reserved.

from abc import ABCMeta, abstractmethod
from functools import wraps
import logging
import time
from typing import Any, Callable, Dict, List, Sequence, Tuple


class AbstractTraceCollector(metaclass=ABCMeta):
    @abstractmethod
    def create_span(self, func) -> Callable[[], None]:
        '''Returns callback to be executed at the end of span.'''
        raise NotImplementedError()


class CummulativeFunctionTimeProfiler(AbstractTraceCollector):
    def __init__(self, *args, **kwargs):
        self.func_times = {}

    def create_span(self, func) -> Callable[[], None]:
        current_time = time.time()

        def store_time():
            t = time.time() - current_time
            t += self.func_times.get(func.__qualname__, 0)
            self.func_times[func.__qualname__] = t

        return store_time

    def summary(self) -> Sequence[Tuple[str, float]]:
        return sorted(self.func_times.items(), key=lambda kv: kv[1])

    def __str__(self) -> str:
        return str(self.summary())


class Timeline(AbstractTraceCollector):
    def __init__(self, *args, **kwargs):
        self._timeline = []

    @property
    def timeline(self):
        return self._timeline

    def create_span(self, func) -> Callable[[], None]:
        self.timeline.append('{t}: ENTRY {n}'.format(
            t=time.time(),
            n=func.__qualname__,
        ))

        return lambda: self.timeline.append('{t}: EXIT {n}'.format(
            t=time.time(),
            n=func.__qualname__,
        ))

    def __str__(self) -> str:
        return str(self.timeline)


TRACE_COLLECTORS = {
    x.__module__ + '.' + x.__qualname__:
        x for x in AbstractTraceCollector.__subclasses__()
}


_trace_collectors: List[AbstractTraceCollector] = []


def set_trace_collectors(collectors: Sequence[AbstractTraceCollector]) -> None:
    global _trace_collectors
    _trace_collectors.clear()
    _trace_collectors += collectors


def configure_tracing(config: Dict[str, Any]) -> None:
    set_trace_collectors([
        TRACE_COLLECTORS[k](v) for k, v in config.items()  # type: ignore
    ])


def trace(collectors: Sequence[AbstractTraceCollector] = _trace_collectors):
    def tracing_decorator(func):
        @wraps(func)
        def with_tracing(*args, **kwargs):
            span_callbacks = [x.create_span(func) for x in collectors]
            try:
                return func(*args, **kwargs)
            finally:
                for f in span_callbacks:
                    f()
        return with_tracing
    return tracing_decorator


def trace_log(
    logger: logging.Logger,
    collectors: Sequence[AbstractTraceCollector] = _trace_collectors
) -> None:
    for tc in collectors:
        logger.info('Trace Collector: {t}: {r}'.format(
            t=tc.__class__.__name__,
            r=str(tc)
        ))
