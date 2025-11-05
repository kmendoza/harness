import time

from bqm.harness import Launcher
from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


class Foo:
    def __call__(self, *args):
        SEC = 10

        print(" ----> user task START")

        t0 = time.time()
        while 1 < 2:
            print(".", end="")
            if time.time() - t0 > SEC:
                print(f"Finished running due to {time.time() - t0:.1f} s")
                break
            time.sleep(1)

        print("\n <---- DONE user task")


Launcher(job=Foo())
