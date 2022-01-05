from contextlib import contextmanager

from . import log
from .base import Target


class Telemeter:
    """The instrumentation interface"""

    def __init__(self, target=None, span=None, *tagdicts) -> None:
        self.target = target if target is not None else Target()
        self.span = span if span is not None else self.target.start()
        self.tags = dict()
        for tags in tagdicts:
            self.tags.update(tags)

    def _merge(self, tagdicts):
        tags = self.tags.copy()
        for d in tagdicts:
            tags.update(d)
        return tags

    """Tracing Methods"""

    @contextmanager
    def child(self, name, *tagdicts):
        child = self.start(name, *tagdicts)
        yield child
        child.finish()

    def start(self, name, *tagdicts):
        tags = self._merge(tagdicts)
        span = self.target.start(self.span, name)
        return Telemeter(self.target, span, tags)

    def finish(self, *tagdicts):
        self.span.finish()
        tags = self._merge(tagdicts)
        self.target.finish(tags, self.span)

    def event(self, name, *tagdicts):
        tags = self._merge(tagdicts)
        self.target.event(name, tags, self.span)

    """Logging methods"""

    def debug(self, message, *tagdicts):
        if self.target.accepts_log_level(log.DEBUG):
            tags = self._merge(tagdicts)
            self.target.log(log.DEBUG, message, tags, self.span)

    def info(self, message, *tagdicts):
        if self.target.accepts_log_level(log.INFO):
            tags = self._merge(tagdicts)
            self.target.log(log.INFO, message, tags, self.span)

    def warning(self, message, *tagdicts):
        if self.target.accepts_log_level(log.WARNING):
            tags = self._merge(tagdicts)
            self.target.log(log.WARNING, message, tags, self.span)

    """Error methods"""

    def error(self, message, exception, *tagdicts):
        tags = self._merge(tagdicts)
        self.target.error(message, exception, tags, self.span)

    """Metrics methods"""

    def magnitude(self, name, value, *tagdicts):
        # TODO: check that value is a number
        tags = self._merge(tagdicts)
        self.target.magnitude(name, value, tags, self.span)

    def count(self, name, value, *tagdicts):
        # TODO: check that value is an integer
        tags = self._merge(tagdicts)
        self.target.count(name, value, tags, self.span)
