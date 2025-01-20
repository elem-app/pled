from typing import Any, cast

import pytest
from pled import Executor

EXECUTE_MODULE_TEST_CASES = [
    (
        "tests.fixtures.test_execute.dummy",
        dict(includes=["tests.fixtures.test_execute.dummy_dep"]),
        8,
    ),
    (
        "tests.fixtures.test_execute.dummy",
        dict(includes=["tests.fixtures.test_execute.dummy"]),
        11,
    ),
    (
        "tests.fixtures.test_execute.dummy",
        dict(includes=["tests.fixtures.test_execute"]),
        24,
    ),
]


@pytest.mark.parametrize(
    "module_name,options,num_traces",
    EXECUTE_MODULE_TEST_CASES,
)
def test_executor_execute_module(
    module_name: str, options: dict[str, Any], num_traces: int
):
    import json

    executor = Executor(module_name, **options)
    tracer = executor.execute_module()
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == num_traces
    json_traces = tracer.dump_json()
    d = json.loads(json_traces)
    if "dummy_func" in d[0]["function_name"]:
        assert d[0]["args"][0][0] == "flag"


EXECUTE_FUNCTION_TEST_CASES = [
    (
        "tests.fixtures.test_execute.dummy_dep",
        "dummy_dep_func",
        (
            3,
            4,
        ),
        cast(dict[str, Any], {}),
        4,
    ),
]


@pytest.mark.parametrize(
    "module_name,function_name,args,kwargs,num_traces",
    EXECUTE_FUNCTION_TEST_CASES,
)
def test_executor_execute_function(
    module_name: str,
    function_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    num_traces: int,
):
    executor = Executor(module_name)
    tracer = executor.execute_function(function_name, *args, **kwargs)
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == num_traces


def test_executor_object_method():
    executor = Executor("tests.fixtures.test_execute.object")
    tracer = executor.execute_module()
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 4


def test_executor_async_function():
    executor = Executor("tests.fixtures.test_execute.async")
    tracer = executor.execute_function("f1")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 7

    tracer = executor.execute_function("f4")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 10


def test_executor_for_in_generator():
    executor = Executor("tests.fixtures.test_execute.yield")
    tracer = executor.execute_function("f1")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 10


def test_executor_async_generator():
    executor = Executor("tests.fixtures.test_execute.yield")
    tracer = executor.execute_function("f3")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 10


def test_executor_yield_from():
    executor = Executor("tests.fixtures.test_execute.yield")
    tracer = executor.execute_function("f5")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 16


def test_executor_generator_send():
    executor = Executor("tests.fixtures.test_execute.yield")
    tracer = executor.execute_function("f8")
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 6


def test_executor_importas():
    executor = Executor(
        "tests.fixtures.test_execute.importas",
        includes=["tests.fixtures.test_execute.dummy_nested_dep"],
    )
    tracer = executor.execute_module()
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 6


def test_executor_background():
    import time

    executor = Executor("tests.fixtures.test_execute.infinite", background=True)
    tracer = executor.execute_function("f1")
    time.sleep(1)
    print(tracer.format_traces())
    assert len(tracer.format_traces().splitlines()) == 8
