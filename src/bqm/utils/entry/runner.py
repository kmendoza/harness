import types
import importlib
import sys
from bqm.utils.logconfig import make_logger
from bqm.utils.entry.parser import EntryPointParser

logger = make_logger(__name__)


class EntryPointRunner:
    def __init__(self):
        self.analyser = EntryPointParser()

    def analyze_and_prepare(self, python_file: str) -> tuple[types.ModuleType, list[type]]:
        """Analyze file and prepare wrapper classes"""

        # Analyze the file
        analysis = self.analyser.analyze_file(python_file)

        print(f"Analysis of {python_file}:")
        print(f"  Has main block: {analysis['has_main_block']}")
        print(f"  Functions: {len(analysis['functions'])}")
        print(f"  Classes: {len(analysis['classes'])}")
        print(f"  Entry points found: {len(analysis['entry_points'])}")

        # Load the module
        module = self._load_module(python_file)

        # Create wrapper classes for each entry point
        wrapper_classes = []
        for entry_point in analysis["entry_points"]:
            print(f"  Creating wrapper for: {entry_point['description']}")
            try:
                wrapper_class = self.extender.create_wrapper_class(entry_point, module)
                wrapper_classes.append(wrapper_class)
            except Exception as e:
                print(f"    Failed to create wrapper: {e}")

        return module, wrapper_classes

    def _load_module(self, python_file: str) -> types.ModuleType:
        """Load a Python file as a module"""
        spec = importlib.util.spec_from_file_location("target_module", python_file)
        if spec is None:
            raise ImportError(f"Could not load spec for {python_file}")

        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules to handle relative imports
        module_name = f"dynamic_module_{id(module)}"
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Clean up sys.modules on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            raise ImportError(f"Failed to execute module {python_file}: {e}")

        return module


if __name__ == "__main__":
    epr = EntryPointRunner()
    epr.analyze_and_prepare("/home/iztok/work/trading/harness/tests/dynamic_launcher/arbitrary_function.py")
    pass
