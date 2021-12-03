from jot import log
from jot.base import Span, Target


def test_default_constructor():
    target = Target()
    assert target.level == log.WARNING


def test_explicit_constructor():
    target = Target(log.INFO)
    assert target.level == log.INFO


def test_accepts_log_level_equal():
    accepted = False
    target = Target(log.INFO)
    if target.accepts_log_level(log.INFO):
        accepted = True
    assert accepted


def test_accepts_log_level_lt():
    accepted = False
    target = Target(log.INFO)
    if target.accepts_log_level(log.WARNING):
        accepted = True
    assert accepted


def test_accepts_log_level_gt():
    accepted = False
    target = Target(log.WARNING)
    if target.accepts_log_level(log.INFO):
        accepted = True
    assert not accepted


def test_start_root():
    target = Target()
    span = target.start()
    assert type(span.trace_id) is int
    assert span.parent_id is None
    assert type(span.id) is int
    assert span.id != span.trace_id
    assert span.id != span.parent_id


def test_start_child():
    parent = Span(1, 2, 3, "parent")
    target = Target()
    child = target.start(parent, "child")
    assert child.trace_id == parent.trace_id
    assert child.parent_id == parent.id
    assert type(child.id) is int
    assert child.id != child.trace_id
    assert child.id != child.parent_id
