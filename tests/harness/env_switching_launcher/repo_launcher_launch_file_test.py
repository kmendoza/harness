from bqm.harness import EnvSwitchingRepoLauncher

EnvSwitchingRepoLauncher(
    config={
        "source": {
            "repo": "git@github.com:kmendoza/harness_test.git",
            "branch": "test-branch",
            "use-local": True,
            "workdir": "/data/tmp/",
            "src-subfolder": "src",
            # "file-to-run":"module/main.py",
            # "entry-point":"__main__",
            "file-to-run": "module/long_running_test.py",
            "entry-point": "xyz",
        },
        "env": {
            "name": "htest3",
        },
        "harness": {
            "interface": "0.0.0.0",
            "port": 3333,
        },
        "target-config": {
            "a": 1,
            "b": [1, 2, 3, 4, 5],
        },
    },
)
