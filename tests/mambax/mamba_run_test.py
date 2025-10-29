import unittest
from bqm.utils.mamba.mambax import Mamba


class MambaTests(unittest.TestCase):
    def test_env_run(self):
        test_env = "XXXXXXXX-unit-test-YYYYYY"
        mamba = Mamba()

        pckg_names = ["pandas", "numpy", "pytz", "simplefix"]
        pckg_vers = ["2.2.0", "1.26.4", None, ""]

        # if mamba.env_exists(test_env):
        #     mamba.remove_env(test_env, waive_safety=True)
        mamba.run(env="htest", file="/home/iztok/work/hwork/harness_test/src/module/main.py")


if __name__ == "__main__":
    unittest.main()
