from bqm.harness import RepoLauncher


RepoLauncher(
    config={
        "source": {
            "repo": "git@github.com:kmendoza/harness_test.git",
            "branch": "test-branch",
            "use-local": True,
            "workdir": "/data/tmp/",
            "src-subfolder":"src",
            "file-to-run":"module/main.py",
        },
       
        "harness": {
            "interface": "0.0.0.0",
            "port": 3000,
        },
        "target-config": {
            "a": 1,
            "b": [1, 2, 3, 4, 5],
        },
        "logging": {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                },
                "app-formatter": {
                    "format": "custom-logger %(name)s %(asctime)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "app-handler": {
                    "class": "logging.StreamHandler",
                    "formatter": "app-formatter",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "myapp": {
                    "level": "INFO",
                    "handlers": ["app-handler"],
                    "propagate": False,
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["console"],
                },
            },
        },
    },
)
