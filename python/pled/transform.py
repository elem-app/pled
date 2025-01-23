import ast
import typing as t

TRACING_FUNCS = ast.parse("""
def __pled_trace_fentry__(func_name, args):
    __pled_tracer.trace_fentry(func_name, [(name, repr(value)) for name, value in args])
def __pled_trace_fexit__(func_name, return_value=None):
    __pled_tracer.trace_fexit(func_name, repr(return_value) if return_value is not None else None)
    return return_value
def __pled_trace_branch__(func_name, branch_type, condition_expr, evaluated_values, condition_result):
    __pled_tracer.trace_branch(func_name, branch_type, condition_expr, [(name, repr(value)) for name, value in evaluated_values], bool(condition_result))
async def __pled_trace_await__(func_name, await_expr, await_value):
    result = await await_value
    __pled_tracer.trace_await(func_name, await_expr, repr(await_value), repr(result))
    return result
def __pled_wrap_generator__(func_name, gen, explicit_return=False):
    it = None
    if hasattr(gen, "send"):
        def __pled_trace_yield(prev_value):
            yield_value = gen.send(prev_value)
            __pled_tracer.trace_yield(func_name, repr(yield_value))
            return yield_value
    elif hasattr(gen, "__next__"):
        def __pled_trace_yield(prev_value):
            yield_value = next(gen)
            __pled_tracer.trace_yield(func_name, repr(yield_value))
            return yield_value
    else:
        it = iter(gen)
        def __pled_trace_yield(prev_value):
            return next(it)
    value = yield __pled_trace_yield(None)
    while True:
        try:
            if it is None:
                __pled_tracer.trace_yield_resume(func_name, repr(value))
            value = yield __pled_trace_yield(value)
        except StopIteration as e:
            if explicit_return:
                __pled_tracer.trace_fexit(func_name, e.value)
            return
async def __pled_wrap_async_generator__(func_name, gen):
    if hasattr(gen, "asend"):
        async def __pled_trace_yield(prev_value):
            yield_value = await gen.asend(prev_value)
            __pled_tracer.trace_yield(func_name, repr(yield_value))
            return yield_value
    else:
        async def __pled_trace_yield(prev_value):
            yield_value = await anext(gen)
            __pled_tracer.trace_yield(func_name, repr(yield_value))
            return yield_value
    value = yield await __pled_trace_yield(None)
    while True:
        try:
            __pled_tracer.trace_yield_resume(func_name, repr(value))
            value = yield await __pled_trace_yield(value)
        except StopAsyncIteration:
            __pled_tracer.trace_fexit(func_name, None)
            return
""").body


class TracingTransformer(ast.NodeTransformer):
    def __init__(self, module_name: str):
        super().__init__()
        self.function_stack: list[str] = []
        self.class_stack: list[str] = [""]  # Track containing classes
        self.module_name = module_name

    @property
    def current_function(self):
        return self.function_stack[-1] if self.function_stack else None

    def visit_Module(self, node: ast.Module) -> ast.AST:
        node.body = TRACING_FUNCS + node.body
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.class_stack.append(node.name)
        result = self.generic_visit(node)
        self.class_stack.pop()
        return result

    def get_qualified_name(self, name: str) -> str:
        """Get fully qualified name including class hierarchy."""
        return f"{self.module_name}{'.'.join(self.class_stack)}.{name}"

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        if node.name.startswith("__pled_inner_gen"):
            node.body = [self.visit(n) for n in node.body]
            return node

        # Skip instrumenting the tracing functions themselves
        if node.name.startswith("__pled_"):
            return node

        # Check if this is an async generator function
        is_generator = False
        has_returns = False

        # Async functions cannot have both yield and return
        for n in ast.walk(node):
            if isinstance(n, ast.Yield):
                is_generator = True
                break
            elif isinstance(n, ast.Return):
                has_returns = True
                break

        qualified_name = self.get_qualified_name(node.name)

        # Create the tracing wrapper
        trace_fentry = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__pled_trace_fentry__", ctx=ast.Load()),
                args=[
                    ast.Constant(value=qualified_name),
                    ast.List(
                        elts=[
                            ast.Tuple(
                                elts=[
                                    ast.Constant(value=arg.arg),
                                    ast.Name(id=arg.arg, ctx=ast.Load()),
                                ],
                                ctx=ast.Load(),
                            )
                            for arg in node.args.args + node.args.kwonlyargs
                        ],
                        ctx=ast.Load(),
                    ),
                ],
                keywords=[],
            )
        )

        if is_generator:
            # Create an inner async generator function with the original code
            inner_gen = ast.AsyncFunctionDef(
                name="__pled_inner_gen",
                args=node.args,
                body=node.body,
                decorator_list=[],
                returns=node.returns,
            )
            marked_return = ast.Return(
                value=ast.Call(
                    func=ast.Name(id="__pled_wrap_async_generator__", ctx=ast.Load()),
                    args=[
                        ast.Constant(value=qualified_name),
                        ast.Call(  # Call the inner generator
                            func=ast.Name(id="__pled_inner_gen", ctx=ast.Load()),
                            args=[
                                ast.Name(id=arg.arg, ctx=ast.Load())
                                for arg in node.args.args
                            ],
                            keywords=[],
                        ),
                    ],
                    keywords=[],
                )
            )
            setattr(marked_return, "__pled_marked_ast__", True)

            # Wrap the generator function's return value
            new_node = ast.FunctionDef(
                name=node.name,
                args=node.args,
                body=[
                    inner_gen,  # First define the inner generator
                    trace_fentry,
                    marked_return,
                ],
                decorator_list=node.decorator_list,
                returns=node.returns,
            )
        else:
            # Store original return statements
            return_wrapper = ast.Try(
                body=node.body,
                handlers=[],
                orelse=[],
                finalbody=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="__pled_trace_fexit__", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=qualified_name),
                                ast.Constant(value=None),
                            ],
                            keywords=[],
                        )
                    )
                    if not has_returns
                    else ast.Pass()
                ],
            )

            # Update the function body
            node.body = [trace_fentry, return_wrapper]
            new_node = node

        self.function_stack.append(qualified_name)
        result = self.generic_visit(new_node)
        self.function_stack.pop()
        return result

    def visit_Await(self, node: ast.Await) -> ast.AST:
        """Trace await expressions"""
        if not self.current_function:
            return node

        return ast.Await(
            value=ast.Call(
                func=ast.Name(id="__pled_trace_await__", ctx=ast.Load()),
                args=[
                    ast.Constant(value=self.current_function),
                    ast.Constant(value=ast.unparse(node.value)),
                    node.value,
                ],
                keywords=[],
            )
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name.startswith("__pled_inner_gen"):
            node.body = [self.visit(n) for n in node.body]
            return node

        # Skip instrumenting the tracing functions themselves
        if node.name.startswith("__pled_"):
            return node

        # Check if this is a generator function
        is_generator = False
        has_returns = False
        for n in ast.walk(node):
            if isinstance(n, (ast.Yield, ast.YieldFrom)):
                is_generator = True
            elif isinstance(n, ast.Return):
                has_returns = True

            if is_generator and has_returns:
                break

        qualified_name = self.get_qualified_name(node.name)

        # Create the tracing wrapper as before
        trace_fentry = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="__pled_trace_fentry__", ctx=ast.Load()),
                args=[
                    ast.Constant(value=qualified_name),
                    ast.List(
                        elts=[
                            ast.Tuple(
                                elts=[
                                    ast.Constant(value=arg.arg),
                                    ast.Name(id=arg.arg, ctx=ast.Load()),
                                ],
                                ctx=ast.Load(),
                            )
                            for arg in node.args.args + node.args.kwonlyargs
                        ],
                        ctx=ast.Load(),
                    ),
                ],
                keywords=[],
            )
        )

        if is_generator:
            # Create an inner generator function with the original code
            inner_gen = ast.FunctionDef(
                name="__pled_inner_gen",
                args=node.args,
                body=node.body,
                decorator_list=[],
                returns=node.returns,
            )
            marked_return = ast.Return(
                value=ast.Call(
                    func=ast.Name(id="__pled_wrap_generator__", ctx=ast.Load()),
                    args=[
                        ast.Constant(value=qualified_name),
                        ast.Call(  # Call the inner generator
                            func=ast.Name(id="__pled_inner_gen", ctx=ast.Load()),
                            args=[
                                ast.Name(id=arg.arg, ctx=ast.Load())
                                for arg in node.args.args
                            ],
                            keywords=[],
                        ),
                        ast.Constant(value=not has_returns),
                    ],
                    keywords=[],
                )
            )
            setattr(marked_return, "__pled_marked_ast__", True)

            # Wrap the generator function's return value
            node.body = [
                inner_gen,  # First define the inner generator
                trace_fentry,
                marked_return,
            ]

        else:
            return_wrapper = ast.Try(
                body=node.body,
                handlers=[],
                orelse=[],
                finalbody=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="__pled_trace_fexit__", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=qualified_name),
                                ast.Constant(value=None),
                            ],
                            keywords=[],
                        )
                    )
                    if not has_returns
                    else ast.Pass()
                ],
            )
            node.body = [trace_fentry, return_wrapper]

        self.function_stack.append(qualified_name)
        result = self.generic_visit(node)
        self.function_stack.pop()
        return result

    def visit_Return(self, node: ast.Return) -> t.Union[ast.Return, t.List[ast.AST]]:
        if getattr(node, "__pled_marked_ast__", False):
            return node

        value_node = node.value

        # TODO: decide whether we want to trace await expressions in return statements
        if value_node:
            value_node = self.visit(value_node)

        trace_exit = ast.Call(
            func=ast.Name(id="__pled_trace_fexit__", ctx=ast.Load()),
            args=[
                ast.Constant(value=self.current_function),
                value_node if value_node else ast.Constant(value=None),
            ],
            keywords=[],
        )
        return ast.Return(value=trace_exit)

    def _make_condition_trace_nodes(
        self,
        branch_type: t.Literal["if", "while"],
        result_var_name: str,
        test_node: ast.expr,
    ) -> tuple[ast.stmt, ast.stmt]:
        condition_expr = ast.unparse(test_node)
        evaluated_values: list[ast.expr] = [
            ast.Tuple(
                elts=[
                    ast.Constant(value=name.id),
                    ast.Name(id=name.id, ctx=ast.Load()),
                ],
                ctx=ast.Load(),
            )
            for name in ast.walk(test_node)
            if isinstance(name, ast.Name)
        ]
        if test_node:
            test_node = self.visit(test_node)

        return (
            ast.Assign(
                targets=[ast.Name(id=result_var_name, ctx=ast.Store())],
                value=test_node,
            ),
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="__pled_trace_branch__", ctx=ast.Load()),
                    args=[
                        ast.Constant(value=self.current_function),
                        ast.Constant(value=branch_type),
                        ast.Constant(value=condition_expr),
                        ast.List(
                            elts=evaluated_values,
                            ctx=ast.Load(),
                        ),
                        ast.Name(id=result_var_name, ctx=ast.Load()),
                    ],
                    keywords=[],
                )
            ),
        )

    def visit_If(self, node: ast.If) -> ast.AST:
        # Visit the body and orelse parts to handle nested nodes
        node.body = [self.visit(n) for n in node.body]
        node.orelse = [self.visit(n) for n in node.orelse]

        if isinstance(node.test, (ast.Constant, ast.Name)):
            return node

        tmp_result_var = f"__pled_trace_branch_result_{id(node)}"
        assign_node, trace_node = self._make_condition_trace_nodes(
            "if", tmp_result_var, node.test
        )

        # Create a new If node that contains our trace nodes in the body
        # followed by the original if statement
        # This is needed for expanding `elif` into a nested if statement
        new_if = ast.If(
            test=ast.Constant(value=True),  # Always execute the trace
            body=[
                assign_node,
                trace_node,
                ast.If(
                    test=ast.Name(id=tmp_result_var, ctx=ast.Load()),
                    body=node.body,
                    orelse=node.orelse,
                ),
            ],
            orelse=[],
        )

        ast.fix_missing_locations(new_if)
        return new_if

    def visit_While(self, node: ast.While) -> ast.AST | t.Sequence[ast.AST]:
        # Visit the body for nested nodes
        node.body = [self.visit(n) for n in node.body]
        node.orelse = [self.visit(n) for n in node.orelse]

        if isinstance(node.test, (ast.Constant, ast.Name)):
            return node

        tmp_result_var = f"__pled_trace_branch_result_{id(node)}"
        condition_trace_nodes = self._make_condition_trace_nodes(
            "while", tmp_result_var, node.test
        )

        # Replace the test with the traced result
        node.test = ast.Name(id=tmp_result_var, ctx=ast.Load())

        # Wrap the body in try-finally to evaluate condition after each iteration
        node.body = [
            ast.Try(
                body=node.body,
                handlers=[],
                orelse=[],
                finalbody=list(condition_trace_nodes),
            )
        ]

        # Return the initial condition evaluation followed by the while loop
        return [*condition_trace_nodes, node]

    def visit_Try(self, node: ast.Try) -> ast.AST:
        # For try blocks, we'll trace when exceptions occur
        for handler in node.handlers:
            if handler.type:
                if not handler.name:
                    handler.name = f"__pled_exc_{id(handler)}"
                    display_name = "<unnamed>"
                else:
                    display_name = handler.name

                handler.body.insert(
                    0,
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="__pled_trace_branch__", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=self.current_function),
                                ast.Constant(value="except"),
                                ast.Constant(value=ast.unparse(handler.type)),
                                ast.List(
                                    elts=[
                                        ast.Tuple(
                                            elts=[
                                                ast.Constant(value=display_name),
                                                ast.Name(
                                                    id=handler.name, ctx=ast.Load()
                                                ),
                                            ],
                                            ctx=ast.Load(),
                                        )
                                    ],
                                    ctx=ast.Load(),
                                ),
                                ast.Constant(value=True),
                            ],
                            keywords=[],
                        )
                    ),
                )

        return self.generic_visit(node)


def transform_module(source: str, module_name: str) -> ast.Module:
    """Transform a module's source code and all its dependencies."""
    tree = ast.parse(source)
    transformed = TracingTransformer(module_name).visit(tree)
    ast.fix_missing_locations(transformed)
    return transformed
