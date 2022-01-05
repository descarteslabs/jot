import jot
import pytest
from jot.base import Span, Target
from jot.telemeter import Telemeter

LOOZY = {"loozy": 34}


@pytest.fixture
def assert_forwards(mocker):
    def _assert_forwards(method_name, *args):
        # spy on the method
        spy = mocker.spy(jot.active, method_name)

        # call the method
        func = getattr(jot, method_name)
        func(*args)

        # assert the call was forwarded
        spy.assert_called_once_with(*args)

    return _assert_forwards


def test_active():
    assert isinstance(jot.active, Telemeter)


def test_init():
    target = Target()
    jot.init(target, LOOZY)
    assert jot.active.target is target
    assert jot.active.tags == LOOZY
    assert jot.active.span is None


def test_start():
    jot.init(Target(), LOOZY)
    parent = jot.active
    jot.start("child", {"nork": 91})

    assert jot.active is not parent
    assert jot.active.tags["nork"] == 91
    assert type(jot.active.span.trace_id) is int
    assert type(jot.active.span.id) is int
    assert jot.active.span.name == "child"

def test_finish():
    parent = jot.active
    jot.start("child")
    jot.finish()

    assert jot.active is parent


def test_with():
    parent = jot.active
    with jot.span("child", {"lep": 66}) as child:
        assert child is jot.active
        assert child is not parent
        assert child.span.parent_id == parent.span.id
        assert child.tags["lep"] == 66
    assert jot.active is parent


def test_with_trace_id():
    parent = jot.active
    with jot.span("child", trace_id=51) as child:
        assert child is jot.active
        assert child is not parent
        assert child.span.trace_id == 51
        assert child.span.parent_id is None
        assert type(child.span.id) is int
        assert child.span.name == "name"


def test_with_parent_id():
    with jot.span("child", trace_id=51, parent_id=66) as child:
        assert child is jot.active
        assert child.span.trace_id == 51
        assert child.span.parent_id == 66
        assert type(child.span.id) is int
        assert child.span.name == "child"


def test_with_error(mocker):
    spy = mocker.spy(jot.active.target, "error")
    with jot.span("child", {"nork": 6}):
        1 / 0
    spy.assert_called_once()
    assert spy.call_args.args[0] == "Error during child"
    assert isinstance(spy.call_args.args[1], ZeroDivisionError)
    assert spy.call_args.args[2]["nork"] == 6
    assert isinstance(spy.call_args.args[3], Span)
    assert spy.call_args.args[3].parent_id == jot.active.span.id


def test_event(assert_forwards):
    assert_forwards("event", "name", LOOZY)


def test_debug(assert_forwards):
    assert_forwards("debug", "debug message", LOOZY)


def test_info(assert_forwards):
    assert_forwards("info", "info message", LOOZY)


def test_warning(assert_forwards):
    assert_forwards("warning", "warning message", LOOZY)


def test_error(assert_forwards):
    try:
        1 / 0
    except ZeroDivisionError as exc:
        assert_forwards("error", "error message", exc, LOOZY)


def test_magnitude(assert_forwards):
    assert_forwards("magnitude", "temperature", 99.0, LOOZY)


def test_count(assert_forwards):
    assert_forwards("count", "requests", 99, LOOZY)
