import os
import sys
import colorama
import importlib
import contextlib
from pathlib import Path

COLORS = {"red":colorama.Fore.RED, "green":colorama.Fore.GREEN}
IGNORED_DIRECTORIES = {"__pycache__"}

def colored(message, color):
    color = COLORS.get(color, color)
    return color + message + colorama.Style.RESET_ALL

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


def run_test(test):
    try:
        test()
        return True
    except Exception as e:
        return False


def print_status(status):
    if status:
        print(end=colored("PASSED", "green"))
    else:
        print(end=colored("FAILED", "red"))


def main(argv):
    modules = {}
    for target in map(Path, argv[1:] or ["."]):
        modules |= load_test_modules(target)
    for path, module in modules.items():
        for name, test in module.__dict__.items():
            if not callable(test) or not name.startswith("test_"):
                continue
            print(str(path) + "::" + name, end=" ")
            print_status(run_test(test))
            term_width = os.get_terminal_size().columns
            print(f"\x1b[{term_width-6}G[....]")


main(sys.argv)
