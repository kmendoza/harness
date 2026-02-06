from bqm.harness import Launcher
from bqm.utils.logconfig import LogFuzz

logger = LogFuzz.make_logger(__name__)


def foo(self, *args) -> int:
    raise Exception("See what happens")


if __name__ == "__main__":
    rv = Launcher(job=foo)
    assert rv == 1
