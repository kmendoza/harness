import inspect
import types
from abc import ABC, abstractmethod
from typing import Any

from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


class EntryPointExtenderError(Exception):
    pass


class CallableWrapper(ABC):
    """Base class for all entry point wrappers"""

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """Make the wrapper callable"""
        pass

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Get information about this entry point"""
        pass


class EntryPointExtender:
    """Creates callable wrapper classes for entry points"""

    @staticmethod
    def create_wrapper_class(entry_point: dict[str, Any], module: types.ModuleType) -> type[CallableWrapper]:
        """
        Create a wrapper class that makes an entry point callable.

        Args:
            entry_point: Dict with 'type', 'name', 'description', etc.
            module: The loaded module containing the entry point

        Returns:
            A class that wraps the entry point and makes it callable
        """
        entry_type = entry_point.get("type")

        if entry_type == "function":
            return EntryPointExtender._create_function_wrapper(entry_point, module)
        elif entry_type == "main_block":
            return EntryPointExtender._create_main_block_wrapper(entry_point, module)
        elif entry_type == "callable_class":
            return EntryPointExtender._create_class_wrapper(entry_point, module)
        else:
            raise ValueError(f"Unknown entry point type: {entry_type}")

    @staticmethod
    def _create_function_wrapper(entry_point: dict[str, Any], module: types.ModuleType) -> type[CallableWrapper]:
        """Wrap a function entry point"""
        func_name = entry_point.get("name")
        func = getattr(module, func_name)

        class FunctionWrapper(CallableWrapper):
            """Wrapper for function entry point"""

            def __init__(self):
                self.entry_point = entry_point
                self.function = func
                self.name = func_name
                self.description = entry_point.get("description", f"Function: {func_name}")

            def __call__(self, *args, **kwargs):
                """Make the wrapper callable"""
                return self.function(*args, **kwargs)

            def __repr__(self):
                return f"<FunctionWrapper: {self.name}>"

            def get_signature(self):
                """Get the function signature"""
                return inspect.signature(self.function)

            def get_info(self) -> dict[str, Any]:
                """Get information about this entry point"""
                return {
                    "type": "function",
                    "name": self.name,
                    "description": self.description,
                    "signature": str(self.get_signature()),
                    "docstring": inspect.getdoc(self.function),
                }

        return FunctionWrapper

    @staticmethod
    def _create_main_block_wrapper(entry_point: dict[str, Any], module: types.ModuleType) -> type[CallableWrapper]:
        """Wrap a main block entry point"""

        class MainBlockWrapper(CallableWrapper):
            """Wrapper for if __name__ == '__main__' block"""

            def __init__(self):
                self.entry_point = entry_point
                self.module = module
                self.name = "__main__"
                self.description = entry_point.get("description", "Main block execution")

            def __call__(self):
                """Execute the main block by re-executing the module"""
                # This is tricky - the main block already executed when we loaded the module
                # We'd need to extract and re-execute just that code
                # For now, we'll reload the module with __name__ set to __main__
                original_name = self.module.__name__
                try:
                    self.module.__name__ = "__main__"
                    # Re-execute the module code
                    exec(compile(open(self.module.__file__).read(), self.module.__file__, "exec"), self.module.__dict__)
                finally:
                    self.module.__name__ = original_name

            def __repr__(self):
                return f"<MainBlockWrapper: {self.description}>"

            def get_info(self) -> dict[str, Any]:
                """Get information about this entry point"""
                return {
                    "type": "main_block",
                    "name": self.name,
                    "description": self.description,
                }

        return MainBlockWrapper

    @staticmethod
    def _create_class_wrapper(entry_point: dict[str, Any], module: types.ModuleType) -> type[CallableWrapper]:
        """Wrap a class entry point (if it has a __call__ or main method)"""
        class_name = entry_point.get("name")
        cls = getattr(module, class_name)

        class ClassWrapper(CallableWrapper):
            """Wrapper for class entry point"""

            def __init__(self):
                self._entry_point = entry_point
                self._wrapped_class = cls
                self._class_name = class_name
                self._description = entry_point.get("description", f"Class: {class_name}")

            def __call__(self, *args, **kwargs):
                """Instantiate the class and optionally call it"""
                instance = self._wrapped_class()
                # If the instance is callable, return a callable wrapper
                if hasattr(instance, "__call__"):
                    return instance(*args, **kwargs)
                else:
                    raise EntryPointExtenderError(f"ERROR. Wrappeed class {self._class_name} must have the __call__ method implementation.")

            def __repr__(self):
                return f"<ClassWrapper: {self._class_name}>"

            def get_info(self) -> dict[str, Any]:
                """Get information about this entry point"""
                return {
                    "type": "class",
                    "name": self._class_name,
                    "description": self._description,
                    "docstring": inspect.getdoc(self._wrapped_class),
                }

        return ClassWrapper
