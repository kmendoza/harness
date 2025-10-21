import time

from bqm.harness import Launcher
from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


class Foo:
    def __call__(self, *args):
        SEC = 100

        print(" ----> user task START")

        t0 = time.time()
        while 1 < 2:
            if time.time() - t0 > SEC:
                print(f"Finished running due to {time.time() - t0:.1f} s")
                break

        print("\n <---- DONE user task")


Launcher(job=Foo())
