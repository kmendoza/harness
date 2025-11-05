import time

from bqm.harness import Launcher
from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


def foo(self, *args) -> int:

    print(" ----> user task START")
    print("\n <---- DONE user task")
    time.sleep(0.5)
    return -1


if __name__ == "__main__":
    rv = Launcher(job=foo)
    pass
