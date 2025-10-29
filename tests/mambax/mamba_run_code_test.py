import unittest
from bqm.utils.mamba.mambax import Mamba


class MambaTests(unittest.TestCase):
    def test_env_run(self):
        py_code = """
import time

from bqm.harness import Launcher
from bqm.utils.logconfig import make_logger


print(123)
print(__name__)
logger = make_logger(__name__)

class Foo:
    def __call__(self, *args):
        SEC = 10

        print(\" ----> user task START\")

        t0 = time.time()
        while 1 < 2:
            print(\".\")
            if time.time() - t0 > SEC:
                print(f\"Finished running due to {time.time() - t0:.1f} s\")
                break
            time.sleep(1)



Launcher(job=Foo())

"""

        mamba = Mamba()
        res = mamba.run_code(env="harness", code=py_code)
        pass


if __name__ == "__main__":
    unittest.main()
