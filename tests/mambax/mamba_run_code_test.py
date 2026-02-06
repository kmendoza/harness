import unittest

from bqm.utils.mamba.mambax import Mamba


class MambaTests(unittest.TestCase):
    def test_env_run(self):
        py_code = """
import time

from bqm.harness import Launcher
from bqm.utils.logconfig import LogFuzz


print(123)
print(__name__)
logger = LogFuzz.make_logger(__name__)

class Foo:
    def __call__(self, *args):
        SEC = 100

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
        # class MambaTests(unittest.TestCase):
        #     def test_env_run(self):
        #         py_code = """
        # print(123)
        # """

        mamba = Mamba()
        res = mamba.run_code(env="harness", code=py_code)
        pass


if __name__ == "__main__":
    unittest.main()
