from .telemeter import Telemeter
from contextlib import contextmanager as _contextmanager

active = Telemeter()
_stack = []


def _push(telemeter):
    global active
    _stack.append(active)
    active = telemeter


def _pop():
    global active
    active = _stack.pop()


def init(target, tags):
    global active, _stack
    active = Telemeter(target, None, tags)
    _stack = []


def start(*args, **kwargs):
    child = active.start(*args, **kwargs)
    _push(child)


def finish(*args, **kwargs):
    active.finish(*args, **kwargs)
    _pop()


def event(name, *tagdicts):
    return active.event(name, *tagdicts)


def debug(message, *tagdicts):
    return active.debug(message, *tagdicts)


def info(message, *tagdicts):
    return active.info(message, *tagdicts)


def warning(message, *tagdicts):
    return active.warning(message, *tagdicts)


def error(message, exc, *tagdicts):
    return active.error(message, exc, *tagdicts)


def magnitude(name, value, *tagdicts):
    return active.magnitude(name, value, *tagdicts)


def count(name, value, *tagdicts):
    return active.count(name, value, *tagdicts)


@_contextmanager
def span(name, *tagdicts, trace_id=None, parent_id=None):
    if trace_id is None:
        child = active.start(name, *tagdicts)
    else:
        span = active.target.span(trace_id=trace_id, parent_id=parent_id, name=name)
        child = Telemeter(active.target, span, *tagdicts)
    _push(child)

    try:
        yield child
    except Exception as exc:
        child.error(f"Error during {name}", exc)
    finally:
        child.finish()
        _pop()
