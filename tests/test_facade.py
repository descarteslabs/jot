from decimal import DivisionByZero
from itsdangerous import exc
import jot
import pytest
from jot.base import Span, Target
from jot.telemeter import Telemeter
from jot import log
from jot.print import PrintTarget

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


@pytest.fixture(autouse=True)
def init():
    jot.init(Target(level=log.ALL))
    jot.start("test", {"ctx": 1})


@jot.generator("async", {"ctx": 2})
def generator():
    for i in range(0, 2):
        jot.info("before")
        yield i
        jot.info("after")


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
        assert child.span.name == "child"


def test_with_parent_id():
    with jot.span("child", trace_id=51, parent_id=66) as child:
        assert child is jot.active
        assert child.span.trace_id == 51
        assert child.span.parent_id == 66
        assert type(child.span.id) is int
        assert child.span.name == "child"


def test_with_error(mocker):
    spy = mocker.spy(jot.active.target, "error")

    try:
        with jot.span("child", {"nork": 6}):
            1 / 0
    except ZeroDivisionError:
        pass

    spy.assert_called_once()
    print(spy.call_args.args)
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


def test_generator(mocker):
    spy = mocker.spy(jot.active.target, "log")

    with jot.span("create", {"ctx": 3}):
        it = generator()

    with jot.span("iterate", {"ctx": 4}):
        for i in it:
            jot.info("during", {"i": i})
        jot.info("done")

    for c in spy.mock.mock_calls:
        msg = c.args[1]
        ctx = c.args[2]["ctx"]
        if msg == "before":
            assert ctx == 2
        elif msg == "during":
            assert ctx == 4
        elif msg == "after":
            assert ctx == 2
        elif msg == "done":
            assert ctx == 4
        else:
            raise AssertionError("Unexpected log message")


def test_generator_dynamic_tags(mocker):
    spy = mocker.spy(jot.active.target, "log")

    with jot.span("create", {"ctx": 3}):
        tags = {"dynamic": True}
        it = generator(jot_tags=tags)

    for i in it:
        jot.info("during", {"i": i})

    for c in spy.mock.mock_calls:
        msg = c.args[1]
        if msg == "before":
            assert "dynamic" in c.args[2]
        elif msg == "during":
            assert "dynamic" not in c.args[2]


@pytest.mark.skip("No implemented yet")
def test_coroutine(mocker):
    spy = mocker.spy(jot.active.target, "log")
    jot.start("outer", {"ctx": 1})

    @jot.coroutine("async", {"ctx": 2})
    def coroutine():
        try:
            while True:
                val = yield
                jot.info("during", {"val": val})
        except GeneratorExit:
            jot.info("done")

    with jot.span("create", {"ctx": 3}):
        g = coroutine()

    with jot.span("sync", {"ctx": 4}):
        next(g)
        for i in range(0, 2):
            jot.info("before", {"i": i})
            g.send(i)
            jot.info("after", {"i": i})
        g.close()

    jot.finish()

    for c in spy.mock.mock_calls:
        msg = c.args[1]
        ctx = c.args[2].get("ctx")
        val = c.args[2].get("val")
        if msg == "before":
            assert ctx == 4
        elif msg == "during":
            assert ctx == 2
            assert type(val) is int
        elif msg == "after":
            assert ctx == 4
        elif msg == "done":
            assert ctx == 4
