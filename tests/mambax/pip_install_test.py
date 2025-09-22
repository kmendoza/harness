import unittest
from bqm.utils.mamba.mambax import Mamba


class MambaTests(unittest.TestCase):
    def test_pip_packages_installation(self):
        test_env = "XXXXXXXX-unit-test-YYYYYY"
        mamba = Mamba()

        pckg_names = ["pandas", "numpy", "pytz", "simplefix"]
        pckg_vers = ["2.2.0", "1.26.4", None, ""]

        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)

        mamba.create_env(test_env, python_version="3.12")

        initial_packages = mamba.list_packages(env=test_env)

        self.assertTrue(initial_packages.contains("python"))
        self.assertTrue(initial_packages.contains("pip"))

        for p in pckg_names:
            self.assertFalse(initial_packages.contains(p))

        mamba.pip_install(env=test_env, package=pckg_names, version=pckg_vers)

        after_packages = mamba.list_packages(env=test_env)

        for p, v in zip(pckg_names, pckg_vers):
            # check requested packages were installed
            self.assertTrue(after_packages.contains(p))
            # check installed packages were pip packages
            self.assertTrue(after_packages.get(p).is_pip())
            # check a desired version was installed if specified
            if v:
                self.assertTrue(after_packages.get(p).version().startswith(v))

        pass


if __name__ == "__main__":
    unittest.main()
