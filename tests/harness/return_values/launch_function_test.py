import time

from bqm.harness import Launcher
from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


def foo(self, *args) -> int:

    print(" ----> user task START")
    print("\n <---- DONE user task")
    time.sleep(0.5)


def foo0(self, *args) -> int:

    print(" ----> user task START")
    print("\n <---- DONE user task")
    time.sleep(0.5)
    return 0


def foo1(self, *args) -> int:

    print(" ----> user task START")
    print("\n <---- DONE user task")
    time.sleep(0.5)
    return 1


def foo2(self, *args) -> int:

    print(" ----> user task START")
    print("\n <---- DONE user task")
    time.sleep(0.5)
    return 2


if __name__ == "__main__":
    rv = Launcher(job=foo)
    assert rv == 0
    rv = Launcher(job=foo0)
    assert rv == 0
    rv = Launcher(job=foo1)
    assert rv == 1
    rv = Launcher(job=foo2)
    assert rv == 2
