import asyncio
import importlib.util
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from inspect import isawaitable
from typing import Any, Iterator, Sequence

from ._pled import Tracer
from .transform import transform_module


def should_instrument(fullname: str, includes: set[str]) -> bool:
    """Check if a module should be instrumented based on includes list"""
    return any(fullname == inc or fullname.startswith(f"{inc}.") for inc in includes)


class PledImportFinder:
    """Custom import finder that transforms modules before they're executed"""

    instrumenting: set[str] = set()  # Track modules being instrumented

    def __init__(
        self, includes: set[str], tracer: Tracer, output_dir: str | None = None
    ):
        self.includes = includes
        self.tracer = tracer
        self.output_dir = output_dir

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: types.ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname in self.instrumenting:
            return None

        if not should_instrument(fullname, self.includes):
            return None

        # Temporarily remove ourselves from sys.meta_path to avoid recursion
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)

        if spec is None or spec.origin is None:
            return None

        assert spec.loader is not None
        spec.loader = PledImportLoader(
            spec.loader, self.tracer, self.includes, self.output_dir
        )
        return spec


class PledImportLoader(Loader):
    """Custom loader that transforms modules before they're executed"""

    def __init__(
        self,
        original_loader: Loader,
        tracer: Tracer,
        includes: set[str],
        output_dir: str | None = None,
    ):
        self.original_loader = original_loader
        self.tracer = tracer
        self.includes = includes
        self.output_dir = output_dir

    def create_module(self, spec: ModuleSpec):
        # Delegate module creation to the original loader
        return self.original_loader.create_module(spec)

    def get_source(self, fullname: str) -> str | None:
        """Get source code from original loader"""
        get_source = getattr(self.original_loader, "get_source", None)
        if get_source is None:
            return None
        return get_source(fullname)

    def exec_module(self, module: types.ModuleType):
        fullname = module.__name__
        if not should_instrument(fullname, self.includes):
            return self.original_loader.exec_module(module)

        source = self.get_source(fullname)
        if source is None:
            # If we can't get source, fall back to original loader
            return self.original_loader.exec_module(module)

        # Mark module as being instrumented to prevent recursion
        PledImportFinder.instrumenting.add(fullname)
        try:
            transformed = transform_module(source, fullname)
            if self.output_dir:
                import ast
                import os

                os.makedirs(self.output_dir, exist_ok=True)
                with open(os.path.join(self.output_dir, f"{fullname}.py"), "w") as f:
                    f.write(ast.unparse(transformed))

            code = compile(transformed, module.__file__ or "<>", "exec")
            module.__dict__["__pled_tracer"] = self.tracer
            exec(code, module.__dict__)
        finally:
            PledImportFinder.instrumenting.remove(fullname)


@dataclass
class ExecutorOptions:
    """Options for executing a module or function."""

    includes: Sequence[str] | None = None
    output_dir: str | None = None
    background: bool = False


class Executor:
    """An executor loads a module and instruments its dependencies."""

    def __init__(
        self,
        module_name: str,
        *,
        includes: Sequence[str] | None = None,
        output_dir: str | None = None,
        background: bool = False,
    ):
        """Initialize a executor.

        :param module_name: The name of the module to load.
        :param includes: The fully qualified names of the modules to instrument. If
            `None`, the given `module_name` will be instrumented.
        :param output_dir: The directory to write the instrumented modules to.
        :param background: Whether to execute in the background and return the tracer
            immediately when calling `execute_module()` or `execute_function()`.
        """
        self.module_name = module_name
        self.options = self._prepare_options(
            ExecutorOptions(
                includes=includes, output_dir=output_dir, background=background
            )
        )

    def _prepare_options(self, options: ExecutorOptions | None) -> ExecutorOptions:
        if options is None:
            options = ExecutorOptions()
        if options.includes is None:
            options.includes = [self.module_name]
        return options

    @contextmanager
    def _tracer(
        self, includes: Sequence[str], output_dir: str | None
    ) -> Iterator[Tracer]:
        tracer = Tracer()
        finder = PledImportFinder(
            set(includes),
            tracer,
            output_dir,
        )
        original_modules = dict(sys.modules)
        sys.meta_path.insert(0, finder)
        try:
            yield tracer
        finally:
            sys.meta_path.remove(finder)
            for mod_name in list(sys.modules.keys()):
                if mod_name not in original_modules:
                    del sys.modules[mod_name]

    def execute_module(self) -> Tracer:
        """Load and execute the module."""

        options = self.options
        assert isinstance(options.includes, Sequence)
        with self._tracer(options.includes, options.output_dir) as tracer:

            def run_module():
                _ = importlib.import_module(self.module_name)

            if options.background:
                import threading

                thread = threading.Thread(target=run_module, daemon=True)
                thread.start()

            else:
                run_module()

            return tracer

    def execute_function(
        self,
        func_name: str,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Tracer:
        """Load the module and execute a function in it."""

        options = self.options
        assert isinstance(options.includes, Sequence)
        with self._tracer(options.includes, options.output_dir) as tracer:
            module = importlib.import_module(self.module_name)
            func = getattr(module, func_name)

            def run_func():
                result = func(*args, **kwargs)
                if isawaitable(result):
                    asyncio.get_event_loop().run_until_complete(result)

            if options.background:
                import threading

                thread = threading.Thread(target=run_func, daemon=True)
                thread.start()

            else:
                run_func()

            return tracer
