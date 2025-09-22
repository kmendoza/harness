import time

from bqm.utils.logconfig import make_logger

logger = make_logger(__name__)


def foo(self, *args):
    SEC = 100

    print(" ----> user task START")

    i, t0, ii, t00 = 1, time.time(), 0, time.time()
    while 1 < 2:

        # time.sleep(1)
        # if i % 5 == 0:
        #     print()
        if time.time() - t0 > SEC:
            print(f"Finished running due to {time.time() - t0:.1f} s")
            break

        if time.time() - t00 > 5:
            t00 = time.time()
            ii += 1
            self.set_status(status={"ii": ii})

        i += 1
    # 1 / 0
    # raise Exception()
    print("\n <---- DONE user task")


if __name__ == "__main__":
    print(12334)
