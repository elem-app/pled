from typing import Any

class Tracer:
    """A tracer is used to trace the execution of a function.

    It is used at various trace points in the codebase to collect relevant data. The
    trace points and the data collected are:

    - `trace_fentry`: Entry to a function
      - `timestamp`: The time when the function was entered
      - `function_name`: The name of the function
      - `args`: The arguments passed to the function
    - `trace_fexit`: Exit from a function
      - `timestamp`: The time when the function exited
      - `function_name`: The name of the function
      - `return_value`: The return value of the function
    - `trace_branch`: Branching logic (if/else, etc.)
      - `timestamp`: The time when the branch was evaluated
      - `function_name`: The name of the function where the branch is located
      - `condition_expr`: The condition expression
      - `evaluated_values`: The values of the evaluated variables
      - `condition_result`: The result of the condition
    - `trace_await`: Await expression
      - `timestamp`: The time when the await expression was evaluated
      - `function_name`: The name of the function where the await expression is located
      - `await_expr`: The await expression
      - `await_value`: The value of the await expression
      - `await_result`: The result of the await expression
    """

    def __init__(self) -> None: ...
    def trace_fentry(self, function_name: str, args: list[tuple[str, str]]) -> None: ...
    def trace_fexit(
        self, function_name: str, return_value: Any | None = None
    ) -> None: ...
    def trace_branch(
        self,
        function_name: str | None,
        branch_type: str,
        condition_expr: str,
        evaluated_values: list[tuple[str, str]],
        condition_result: bool,
    ) -> None: ...
    def trace_await(
        self,
        function_name: str,
        await_expr: str,
        await_value: str,
        await_result: str,
    ) -> None: ...
    def trace_yield(
        self,
        function_name: str,
        yield_value: str,
    ) -> None: ...
    def trace_yield_resume(self, function_name: str, send_value: str) -> None: ...
    def format_traces(self) -> str:
        """Format the traces as a multiline string."""
    def dump_json(self) -> str:
        """Dump the traces as a stringified JSON."""
    def dump_report_file(self, path: str) -> None:
        """Dump the traces as a HTML report file.

        .. note ::
            You need an internet connection to render the report as it uses Mermaid from
            npm.
        """
