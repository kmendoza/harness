import ast
from typing import Any

from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


class EntryPointParser:
    def __init__(self):
        self.entry_points = []
        self.classes = []
        self.functions = []
        self.top_level_calls = []
        self.has_main_block = False

    def analyze_file(self, filename: str) -> dict[str, Any]:
        """Analyze a Python file to find entry points"""
        with open(filename, "r", encoding="utf-8") as file:
            content = file.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {filename}: {e}")

        self._analyze_ast(tree)

        return {
            "has_main_block": self.has_main_block,
            "functions": self.functions,
            "classes": self.classes,
            "top_level_calls": self.top_level_calls,
            "entry_points": self._determine_entry_points(),
        }

    def _analyze_ast(self, tree: ast.AST):
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
            elif isinstance(node, ast.ClassDef):
                self._analyze_class(node)
            elif isinstance(node, ast.If):
                self._check_main_block(node)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                self._analyze_top_level_call(node.value)

    def _analyze_function(self, node: ast.FunctionDef):
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "has_args": len(node.args.args) > 0,
            "has_defaults": len(node.args.defaults) > 0,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "docstring": ast.get_docstring(node),
            "line_no": node.lineno,
        }

        # Check if it looks like a main function
        if node.name in ["main", "run", "start", "execute"]:
            func_info["is_main_candidate"] = True

        self.functions.append(func_info)

    def _analyze_class(self, node: ast.ClassDef):
        methods = []
        has_call = False
        has_init = False

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                if item.name == "__call__":
                    has_call = True
                elif item.name == "__init__":
                    has_init = True

        class_info = {
            "name": node.name,
            "methods": methods,
            "has_call": has_call,
            "has_init": has_init,
            "is_callable": has_call,
            "docstring": ast.get_docstring(node),
            "line_no": node.lineno,
        }

        self.classes.append(class_info)

    def _check_main_block(self, node: ast.If):
        if (
            isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Eq)
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == "__main__"
        ):
            self.has_main_block = True

    def _analyze_top_level_call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.top_level_calls.append({"function": node.func.id, "args": len(node.args), "keywords": len(node.keywords)})

    def _determine_entry_points(self) -> list[dict[str, Any]]:
        """Determine the best entry points"""
        entry_points = []

        # Priority 1: Main block exists
        if self.has_main_block:
            entry_points.append({"type": "main_block", "name": "__main__", "priority": 1, "description": "Standard __main__ block"})

        # Priority 2: Main-like functions
        for func in self.functions:
            if func.get("is_main_candidate"):
                entry_points.append(
                    {
                        "type": "function",
                        "name": func["name"],
                        "priority": 2,
                        "description": f"Main-like function: {func['name']}",
                        "args": func["args"],
                        "has_args": func["has_args"],
                    }
                )

        # Priority 3: Callable classes
        for cls in self.classes:
            if cls["is_callable"]:
                entry_points.append(
                    {
                        "type": "callable_class",
                        "name": cls["name"],
                        "priority": 3,
                        "description": f"Callable class: {cls['name']}",
                        "has_init": cls["has_init"],
                    }
                )

        # Priority 4: Top-level calls
        for call in self.top_level_calls:
            entry_points.append(
                {"type": "top_level_call", "name": call["function"], "priority": 4, "description": f"Top-level call: {call['function']}()"}
            )

        # Priority 5: Any function without args
        for func in self.functions:
            if not func["has_args"] and not func.get("is_main_candidate"):
                entry_points.append(
                    {
                        "type": "function",
                        "name": func["name"],
                        "priority": 5,
                        "description": f"Parameter-less function: {func['name']}",
                        "args": func["args"],
                    }
                )

        return sorted(entry_points, key=lambda x: x["priority"])


# if __name__ == "__main__":
#     ep = EntryPointParser()
#     analysis = ep.analyze_file("/home/iztok/work/trading/harness/tests/cradle_test_consul.py")
#     pass
