import unittest
from bqm.utils.mamba import Mamba, MambaError


class MambaTests(unittest.TestCase):
    def test_env_creation(self):
        test_env = "XXXXXXXX-unit-test-YYYYYY"
        mamba = Mamba()

        # clean up before the tests
        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)
        print(f"before creation: {mamba.existing_environments()}")

        # check that test env does not exist
        self.assertFalse(mamba.env_exists(test_env))
        self.assertFalse(test_env in mamba.existing_environments())

        # create env, test that it exists afters
        mamba.create_env(test_env)
        print(f"after creation: {mamba.existing_environments()}")
        self.assertTrue(mamba.env_exists(test_env))
        self.assertTrue(test_env in mamba.existing_environments())

        # check that we are prevented from creating another env
        with self.assertRaises(MambaError):
            mamba.create_env(test_env)

        # check that env is correctlly removed
        mamba.remove_env(test_env, waive_safety=True)
        print(f"after deletion: {mamba.existing_environments()}")
        self.assertFalse(mamba.env_exists(test_env))
        self.assertFalse(test_env in mamba.existing_environments())

        # create env, test that it exists afters
        PY_VER = "3.13"
        mamba.create_env(test_env, python_version=PY_VER)
        print(f"after creation: {mamba.existing_environments()}")
        self.assertTrue(mamba.env_exists(test_env))
        self.assertTrue(test_env in mamba.existing_environments())
        pkgs = mamba.list_packages(env=test_env)
        self.assertTrue(pkgs.contains("python"))
        self.assertTrue(pkgs.get("python").version().startswith(PY_VER))


if __name__ == "__main__":
    unittest.main()
