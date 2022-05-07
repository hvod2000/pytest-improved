import sys
import importlib
import contextlib
from pathlib import Path

IGNORED_DIRECTORIES = {"__pycache__"}


def load_test_module(path):
    if spec := importlib.util.spec_from_file_location(path.stem, path):
        module = importlib.util.module_from_spec(spec)
        with contextlib.suppress(Exception):
            spec.loader.exec_module(module)
            return module


def load_test_modules(path):
    result = {}
    if path.is_file():
        if module := load_test_module(path):
            result[path] = module
    if path.is_dir() and path.stem not in IGNORED_DIRECTORIES:
        for path in path.iterdir():
            result |= load_test_modules(path)
    return result


def main(argv):
    modules = {}
    for target in map(Path, argv[1:] or ["."]):
        modules |= load_test_modules(target)
    for path, module in modules.items():
        for name, f in module.__dict__.items():
            if not callable(f) or not name.startswith("test_"):
                continue
            print(str(path) + "::" + name, end=" ")
            try:
                f()
                print("PASSED")
            except Exception as e:
                print("FAILED")


main(sys.argv)
