import unittest

from bqm.utils.mamba import Mamba


class MambaTests(unittest.TestCase):
    def test_mamba_packages_installation(self):
        test_env = "XXXXXXXX-unit-test-YYYYYY"
        mamba = Mamba()

        pckg_specs = ["python=3.13.9=h2b335a9_100_cp313", "jsonschema=4.25.1=pyhe01879c_0"]

        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)

        mamba.create_env(test_env)
        self.assertTrue(mamba.env_exists(test_env))

        log = mamba.install_specs(env=test_env, spec=pckg_specs, channel="conda-forge")
        packages = mamba.list_packages(env=test_env)

        for ps in pckg_specs:
            p, v, b = ps.split("=")
            # check requested packages were installed
            self.assertTrue(packages.contains(p))
            # check a desired version was installed if specified
            if v:
                self.assertTrue(packages.get(p).version().startswith(v))

        pass


if __name__ == "__main__":
    unittest.main()
