import unittest
from bqm.utils.mamba import Mamba


class MambaTests(unittest.TestCase):
    def test_mamba_packages_installation(self):
        test_env = "XXXXXXXX-unit-test-YYYYYY"
        mamba = Mamba()

        pckg_names = ["python", "pandas", "numpy", "pytz", "yaml"]
        pckg_vers = ["3.12", "2.2.0", "1.26.4", None, ""]

        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)

        mamba.create_env(test_env)
        self.assertTrue(mamba.env_exists(test_env))

        log = mamba.install(env=test_env, package=pckg_names, version=pckg_vers, channel="conda-forge")
        packages = mamba.list_packages(env=test_env)

        for p, v in zip(pckg_names, pckg_vers):
            # check requested packages were installed
            self.assertTrue(packages.contains(p))
            # check a desired version was installed if specified
            if v:
                self.assertTrue(packages.get(p).version().startswith(v))

        pass


if __name__ == "__main__":
    unittest.main()
