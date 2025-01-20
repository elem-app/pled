# pled – print-less debugging

pled is a library for debugging Python code so you don't have to paste `print()` everywhere.

It features no-code instrumentation on your codebase.

## Getting started

1. Install `pled` as a library

   ```bash
   # With poetry
   poetry add --dev pled

   # With uv
   uv add --dev pled
   ```

2. Use an executor to execute code and collect traces into a tracer

   ```python
   # Tracing function `bar(*args, **kwargs)` inside module `foo`

   from pled import Executor

   executor = Executor("foo")
   tracer = executor.execute_function("bar", *args, **kwargs)
   ```

3. Inspect the traces in a tracer

   ```python
   # Print the traces
   print(tracer.format_traces())

   # Or dump into stringified JSON
   json_traces = tracer.dump_json()
   ```

## Types of traces

pled traces the following types of events:

- `FunctionEntry` - function entry
  - `function_name` - fully qualified function name
  - `args` - the full argument list in name-value pairs
  - `timestamp` - timestamp of the event
- `FunctionExit` - function exit
  - `function_name` - fully qualified function name
  - `return_value` - return value
  - `timestamp` - timestamp of the event
- `Branch` - branching
  - `function_name` - fully qualified function name where the branch is located
  - `branch_type` - branch type, can be `if`, `while`, or `except`
  - `condition_expr` - condition expression
  - `evaluated_values` - evaluated values
  - `condition_result` - condition result
  - `timestamp` - timestamp of the event
- `Await` - await expression
  - `function_name` - fully qualified function name where the await is located
  - `await_expr` - await expression
  - `await_value` - value being awaited
  - `await_result` - result of the await
  - `timestamp` - timestamp of the event
- `Yield` - yield expression
  - `function_name` - fully qualified function name where the yield is located
  - `yield_value` - value being yielded
  - `timestamp` - timestamp of the event
- `YieldResume` - yield resumption
  - `function_name` - fully qualified function name where the yield is located
  - `send_value` - value being sent to the generator
  - `timestamp` - timestamp of the event

Note: `timestamp` is a float representing the number of seconds since the _start of the
execution_.

## Examples

### Tracing a module

Given this module:

```python
# Module: your_project.main

def just_print():
    print("hello")

just_print()  # <-- this module does some work directly
```

You can trace the execution of this module by running:

```python
from pled import Executor

executor = Executor("your_project.main")
tracer = executor.execute_module()
print(tracer.format_traces())
```

### Tracing a function

Given this module without root-level execution:

```python
# Module: your_project.add

def just_add(a: int, b: int) -> int:
    return a + b
```

You can trace the execution of a function by running:

```python
from pled import Executor

executor = Executor("your_project.add")
tracer = executor.execute_function("just_add", 1, 2)
print(tracer.format_traces())
```

### Tracing multiple modules

You can trace multiple modules by passing a list of package or module names to the
`Executor` constructor.

Suppose you want to trace everything inside `your_project` package when executing
`your_project.add.just_add` function.

```python
from pled import Executor

executor = Executor("your_project.add", includes=["your_project"])
tracer = executor.execute_function("just_add", 1, 2)
print(tracer.format_traces())
```

### Tracing a function with background execution

You can run the executor in the background by setting the `background` option to `True`.

Given this module:

```python
# Module: your_project.event_loop

def infinite_yield():
    import time

    while True:
        time.sleep(0.5)
        yield 1

def loop():
    for _ in infinite_yield():
        pass
```

You can run `loop()` in the background with:

```python
from pled import Executor

executor = Executor("your_project.event_loop", background=True)
tracer = executor.execute_function("loop")
while True:
    time.sleep(1)
    print(tracer.format_traces())
```
