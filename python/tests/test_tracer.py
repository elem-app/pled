import pytest
from pled._pled import Tracer


@pytest.fixture
def tracer():
    return Tracer()


def test_trace_fentry(tracer: Tracer):
    # Test with valid arguments
    tracer.trace_fentry("test_function", [("arg1", "1"), ("arg2", "2")])

    # Test with empty args list
    tracer.trace_fentry("test_function", [])

    # Test with None function_name
    with pytest.raises(TypeError):
        tracer.trace_fentry(None, [("arg1", "1"), ("arg2", "2")])  # pyright: ignore[reportArgumentType]

    # Test with None args
    with pytest.raises(TypeError):
        tracer.trace_fentry("test_function", None)  # pyright: ignore[reportArgumentType]

    # Test with missing args
    with pytest.raises(TypeError):
        tracer.trace_fentry("test_function")  # pyright: ignore[reportCallIssue]


def test_trace_fexit(tracer: Tracer):
    # Test with return value
    tracer.trace_fexit("test_function", "return_value")

    # Test with None return value
    tracer.trace_fexit("test_function", None)

    # Test with missing return_value
    tracer.trace_fexit("test_function")

    # Test with None function_name
    with pytest.raises(TypeError):
        tracer.trace_fexit(None, "return_value")  # pyright: ignore[reportArgumentType]


def test_trace_branch(tracer: Tracer):
    # Test with all arguments
    tracer.trace_branch(
        "test_function",
        "if",
        "x > 0",
        [("x", "5")],
        True,
    )

    # Test with empty evaluated_values
    tracer.trace_branch(
        "test_function",
        "if",
        "x > 0",
        [],
        False,
    )

    # Test with None function_name
    tracer.trace_branch(
        None,
        "if",
        "x > 0",
        [],
        False,
    )

    # Test with None branch_type
    with pytest.raises(TypeError):
        tracer.trace_branch(
            "test_function",
            None,  # pyright: ignore[reportArgumentType]
            "x > 0",
            [],
            False,
        )

    # Test with None condition_expr
    with pytest.raises(TypeError):
        tracer.trace_branch(
            "test_function",
            "if",
            None,  # pyright: ignore[reportArgumentType]
            [],
            False,
        )

    # Test with None evaluated_values
    with pytest.raises(TypeError):
        tracer.trace_branch(
            "test_function",
            "if",
            "x > 0",
            None,  # pyright: ignore[reportArgumentType]
            False,
        )

    # Test with missing arguments
    with pytest.raises(TypeError):
        tracer.trace_branch(  # pyright: ignore[reportCallIssue]
            "test_function",
            "if",
            "x > 0",
            [],
        )


def test_trace_await(tracer: Tracer):
    # Test with valid arguments
    tracer.trace_await(
        "async_function",
        "await foo()",
        "<coroutine object>",
        "42",
    )

    # Test with None function_name
    with pytest.raises(TypeError):
        tracer.trace_await(
            None,  # pyright: ignore[reportArgumentType]
            "await foo()",
            "<coroutine object>",
            "42",
        )

    # Test with None await_expr
    with pytest.raises(TypeError):
        tracer.trace_await(
            "async_function",
            None,  # pyright: ignore[reportArgumentType]
            "<coroutine object>",
            "42",
        )

    # Test with missing arguments
    with pytest.raises(TypeError):
        tracer.trace_await("async_function")  # pyright: ignore[reportCallIssue]


def test_trace_yield(tracer: Tracer):
    # Test with valid arguments
    tracer.trace_yield("generator_function", "42")

    # Test with None function_name
    with pytest.raises(TypeError):
        tracer.trace_yield(
            None,  # pyright: ignore[reportArgumentType]
            "42",
        )

    # Test with None yield_value
    with pytest.raises(TypeError):
        tracer.trace_yield(
            "generator_function",
            None,  # pyright: ignore[reportArgumentType]
        )

    # Test with missing yield_value
    with pytest.raises(TypeError):
        tracer.trace_yield("generator_function")  # pyright: ignore[reportCallIssue]


def test_trace_yield_resume(tracer: Tracer):
    # Test with valid arguments
    tracer.trace_yield_resume("generator_function", "next_value")

    # Test with None function_name
    with pytest.raises(TypeError):
        tracer.trace_yield_resume(
            None,  # pyright: ignore[reportArgumentType]
            "next_value",
        )

    # Test with None send_value
    with pytest.raises(TypeError):
        tracer.trace_yield_resume(
            "generator_function",
            None,  # pyright: ignore[reportArgumentType]
        )

    # Test with missing send_value
    with pytest.raises(TypeError):
        tracer.trace_yield_resume("generator_function")  # pyright: ignore[reportCallIssue]


def test_format_traces(tracer: Tracer):
    # Add some traces first
    tracer.trace_fentry("test_function", [("arg1", "1")])
    tracer.trace_fexit("test_function", "result")

    # Test format_traces returns a string
    result = tracer.format_traces()
    assert isinstance(result, str)
    assert len(result.splitlines()) == 2


def test_dump_json(tracer: Tracer):
    import json

    tracer.trace_fentry("test_function", [("arg1", "1")])
    tracer.trace_fexit("test_function", "result")

    s = tracer.dump_json()
    assert isinstance(s, str)
    assert len(s) > 0

    d = json.loads(s)
    assert isinstance(d, list)
    assert len(d) == 2  # type: ignore
    assert d[0]["type"] == "FunctionEntry"
    assert d[1]["type"] == "FunctionExit"


def test_dump_report_file(tracer: Tracer):
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".html", dir=".") as tmpfile:
        tracer.trace_fentry("test_function", [("arg1", "1")])
        tracer.trace_fexit("test_function", "result")

        tracer.dump_report_file(tmpfile.name)
        assert os.path.exists(tmpfile.name)
