import os
import sys
import time
import colorama
import importlib
import contextlib
from pathlib import Path


TERM_WIDTH = os.get_terminal_size().columns
COLORS = {"red": colorama.Fore.RED, "green": colorama.Fore.GREEN}
IGNORED_DIRECTORIES = {"__pycache__"}


def print_header(header):
    left = (TERM_WIDTH - len(header)) // 2 - 1
    right = TERM_WIDTH - left - len(header) - 2
    print("=" * left, header, "=" * right)


def colored(message, color):
    color = COLORS.get(color, color)
    return color + message + colorama.Style.RESET_ALL


def bolded(message):
    return "\x1b[1m" + message + "\x1b[0m"


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


def load_tests(module):
    result = {}
    for name, test in module.__dict__.items():
        if not callable(test) or not name.startswith("test_"):
            continue
        result[name] = test
    return result


def run_test(test):
    try:
        test()
        return (True, None)
    except Exception:
        e_type, e, trace = sys.exc_info()
        path = Path(trace.tb_next.tb_frame.f_code.co_filename)
        line = trace.tb_next.tb_lineno - 1
        return (False, (e, path, line))


def print_status(status):
    if status:
        print(end=colored("PASSED", "green"))
    else:
        print(end=colored("FAILED", "red"))


def main(argv):
    modules = {}
    print("rootdir:", Path(".").resolve())
    print("collecting ...", end="")
    for target in map(Path, argv[1:] or ["."]):
        modules |= load_test_modules(target)
    testsets = {name: load_tests(m) for name, m in modules.items()}
    total_tests, current_test = sum(map(len, testsets.values())), 0
    fails, t0 = {}, time.time()
    print(bolded(f"\x1b[1Gcollected {total_tests} items"))
    print()
    for module_path, testset in testsets.items():
        for name, test in testset.items():
            current_test += 1
            print(str(module_path) + "::" + name, end=" ")
            success, error = run_test(test)
            if not success:
                fails[str(module_path) + "::" + name] = error
            print_status(success)
            term_width = os.get_terminal_size().columns
            percents = str(round(current_test / total_tests * 100)) + "%"
            color = "red" if fails else "green"
            print(colored(f"\x1b[{term_width-6}G[{percents:>4}]", color))
    print()
    print_header("short test summary info")
    for path, (e, e_path, e_line) in fails.items():
        print("FAILED", path, e_path.read_text().split("\n")[e_line].strip())
    failed = len(fails)
    passed = total_tests - len(fails)
    dt = time.time() - t0
    print_header(f"{failed} failed, {passed} passed in {dt:0.2f}s")


main(sys.argv)
