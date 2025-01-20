"""Fixtures for testing the execute module.

This module contains the following scenarios:

- Function definition and calling:
  1. Simple module and function - `dummy_nested_dep.py`
  2. Call of a function in an imported module - `dummy_dep.py`
  3. Call of an imported function - `dummy.py`
  4. Call of a function at module level - `dummy.py`
  5. Call of a function in an aliased module - `importas.py`
  6. Call of an aliased function - `importas.py`

- Branching:
  1. `if`-`elif`-`else` - `dummy.py`
  2. `while` - `dummy_dep.py`
  3. `except` one error - `dummy_nested_dep.py`

- Async/await:
  1. `async` function - `async.py`
  2. Function returning coroutine - `async.py`
  3. `await` expression - `async.py`
  4. `await` expression inside `return` statement - `async.py`
  5. `await` expression inside `if` condition - `async.py`
  6. `await` expression inside `while` condition - `async.py`

- Generators:
  1. `yield` - `yield.py`
  2. Generator - `yield.py`
  3. `send` - `yield.py`
  4. `for` with generator - `yield.py`
  5. Generator with return - `yield.py`
  6. `yield from` - `yield.py`
  7. Async generator - `yield.py`
  8. `async for` with async generator - `yield.py`

"""
