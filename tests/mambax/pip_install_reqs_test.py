import unittest
from bqm.utils.mamba.mambax import Mamba


class MambaTests(unittest.TestCase):

    TST_REQS = """
                bqm-data-api @ git+ssh://git@bitbucket.org/bqmrepo/data-api.git@0ff29ae1cd46ff142dc2f3d648d7fa5c9a7d49f6#subdirectory=src
                certifi==2025.1.31
                clickhouse-connect==0.8.17
                exchange_calendars==4.10
                joblib==1.4.2
                korean-lunar-calendar==0.3.1
                lz4==4.4.4
                numpy==2.2.5
                pandas==2.2.3
                pandas_market_calendars==4.6.1
                pyarrow==19.0.1
                pyluach==2.2.0
                python-dateutil==2.9.0.post0
                pytz==2025.2
                schedule==1.2.2
                six==1.17.0
                toolz==1.0.0
                tzdata==2025.2
                urllib3==2.4.0
                zstandard==0.23.0
                tenacity==9.1.2
                matplotlib==3.10.1
                seaborn==0.13.2
                scipy==1.15.2
                statsmodels==0.14.4
            """

    def prs_pkg(self, ln: str) -> tuple[str, str]:
        if "==" in ln:
            vals = [v.strip() for v in ln.split("==")]
            return vals[0], vals[1]
        elif "@" in ln:
            return ln.split("@")[0].strip(), None
        else:
            raise Exception(f"Dont know how to interpret requiremets line: {ln}")

    def test_pip_install_reqs(self):

        mamba = Mamba()
        test_env = "XXXXXXXX-unit-test-YYYYYY"

        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)

        REQS_FILE = "./tests/mambax/requirements.txt"
        with open(REQS_FILE, "r") as rf:
            expected_pkgs = dict(self.prs_pkg(ln.strip()) for ln in rf.readlines() if ln.strip())

        mamba.create_env(test_env)

        installed_pkgs = mamba.list_packages(env=test_env)
        for p, v in expected_pkgs.items():
            self.assertFalse(installed_pkgs.contains(p))

        # pip must be installed in target environment
        mamba.install(env=test_env, package=["python", "pip"], version=["3.12", None])
        mamba.pip_install_reqs(env=test_env, reqs_file=REQS_FILE)
        installed_pkgs = mamba.list_packages(env=test_env)

        # conda listing compliance is 'soft' (packages names in pip v module names in conda)
        for p, v in expected_pkgs.items():
            self.assertTrue(installed_pkgs.contains(p) or installed_pkgs.contains(p.replace("_", "-")))
            if v:
                if installed_pkgs.contains(p):
                    self.assertTrue(installed_pkgs.get(p).version().startswith(v))
                elif installed_pkgs.contains(p.replace("_", "-")):
                    self.assertTrue(installed_pkgs.get(p.replace("_", "-")).version().startswith(v))
                else:
                    raise Exception("BUG in logic.")

        # pip compliance should be 100%
        installed_PIP_pkgs = mamba.pip_list(env=test_env)
        for p, v in expected_pkgs.items():
            self.assertTrue(p in installed_PIP_pkgs)
            if v:
                self.assertTrue(installed_PIP_pkgs[p].startswith(v))

        self.assertTrue(mamba.pip_verify_reqs(env=test_env, reqs_file=REQS_FILE))

        mamba.remove_env(test_env, waive_safety=True)

    def test_pip_install_reqs_from_str(self):

        mamba = Mamba()
        test_env = "XXXXXXXX-unit-test-YYYYYY"

        expected_pkgs = dict(self.prs_pkg(ln.strip()) for ln in self.TST_REQS.split("\n") if ln.strip())

        if mamba.env_exists(test_env):
            mamba.remove_env(test_env, waive_safety=True)

        mamba.create_env(test_env)

        installed_pkgs = mamba.list_packages(env=test_env)
        for p, v in expected_pkgs.items():
            self.assertFalse(installed_pkgs.contains(p))

        mamba.install(env=test_env, package=["python", "pip"], version=["3.12", None])
        mamba.pip_install_reqs(env=test_env, reqs_str=self.TST_REQS)
        installed_pkgs = mamba.list_packages(env=test_env)

        for p, v in expected_pkgs.items():
            self.assertTrue(installed_pkgs.contains(p) or installed_pkgs.contains(p.replace("_", "-")))
            if v:
                if installed_pkgs.contains(p):
                    self.assertTrue(installed_pkgs.get(p).version().startswith(v))
                elif installed_pkgs.contains(p.replace("_", "-")):
                    self.assertTrue(installed_pkgs.get(p.replace("_", "-")).version().startswith(v))
                else:
                    raise Exception("BUG in logic.")

        # pip compliance should be 100%
        installed_PIP_pkgs = mamba.pip_list(env=test_env)
        for p, v in expected_pkgs.items():
            self.assertTrue(p in installed_PIP_pkgs)
            if v:
                self.assertTrue(installed_PIP_pkgs[p].startswith(v))

        self.assertTrue(mamba.pip_verify_reqs(env=test_env, reqs_str=self.TST_REQS))

        mamba.remove_env(test_env, waive_safety=True)


if __name__ == "__main__":
    unittest.main()
