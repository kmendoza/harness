import queue
from abc import ABC, abstractmethod
from multiprocessing import Queue
from typing import Any

from bqm.harness.commands import Command


class ProcessHarnessError(Exception):
    pass


class Cradle(ABC):

    @abstractmethod
    def run(self, *args): ...

    def set_queues(self, command_q: Queue, status_q: Queue):
        self._command_q = command_q
        self._status_q = status_q

    def get_msg(self) -> tuple[Command | None, dict | None]:
        try:
            if not self._command_q.empty():
                return self._command_q.get(block=False)
            else:
                return None
        except queue.Empty:
            return None

    def set_status(self, status: dict[str, Any]) -> bool:
        return self._status_q.put(status)

    def get_config(self) -> dict[str, Any]:
        return self._config

    def __call__(self):
        self.run()
