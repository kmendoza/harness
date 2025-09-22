import asyncio
import json
import logging
import queue
import sys
from multiprocessing import Process, Queue
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from bqm.harness.base import ServiceInterface
from bqm.harness.commands import Command
from bqm.harness.cradle import Cradle
from bqm.harness.msg_factory import MessageFactory

logger = logging.getLogger(__name__)


class ProcessHarnessError(Exception):
    pass


class ProcessHarness(ServiceInterface):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._command_queue = Queue()
        self._status_queue = Queue()
        self._process = None
        self._status = None
        self._request_counts = {}

    async def job_is_alive(self) -> bool:
        return self._process and self._process.is_alive()

    async def _hb(self, req: Request):
        if not await self.job_is_alive():
            return MessageFactory.mk_cmd_err_response(req, cmd=Command.HB, error="Launched process is not alive", process=self._process)
        return MessageFactory.mk_hb_response(req, process=self._process)

    async def __wrap(self, req: Request, cmd: Command) -> JSONResponse:
        if not await self.job_is_alive():
            return MessageFactory.mk_cmd_err_response(req, cmd=cmd, error="Launched process is not alive", process=self._process)

        body = await req.body()
        if body:
            try:
                data = json.loads(body)
            except Exception as e:
                msg = f"Failed to parse json: {body}. {e}"
                logger.error(msg)
                raise ProcessHarnessError(msg)
        else:
            data = {}
        self._command_queue.put({"cmd": cmd, "data": data})
        return MessageFactory.mk_cmd_response(req, cmd, self._process)

    async def _start(self, req: Request) -> JSONResponse:
        return await self.__wrap(req, Command.START)

    async def _stop(self, req: Request) -> JSONResponse:
        return await self.__wrap(req, Command.STOP)

    async def _pause(self, req: Request) -> JSONResponse:
        return await self.__wrap(req, Command.PAUSE)

    async def _resume(self, req: Request) -> JSONResponse:
        return await self.__wrap(req, Command.RESUME)

    async def _data(self, req: Request) -> JSONResponse:
        return await self.__wrap(req, Command.CONFIG)

    async def _status(self, req: Request) -> JSONResponse:
        try:
            while True:
                self._status = self._status_queue.get_nowait()
        except queue.Empty:
            pass
        return MessageFactory.mk_status_response(req, self._status, self._process)

    async def _kill(self, req: Request) -> JSONResponse:
        logger.warning(f"!!!! Received KILL command from address: {req.client}")
        logger.warning(" ------------------------------")
        if self._process:
            self._process.kill()
            logger.warning(f"Killed managed process: {self._process.pid}")
        logger.warning(" ------------------------------")

    async def main(self, job: Cradle) -> int:

        if not isinstance(job, Cradle):
            raise ProcessHarnessError("Job you want to run must inherit from Cradle.")

        job.set_queues(self._command_queue, self._status_queue)

        self._start_server()

        self._process = Process(target=job)
        self._process.start()
        logger.info("+----------")
        logger.info(f"| Launched target process. PID: [{self._process.pid}]")
        logger.info(f"|  argv: {' '.join(sys.argv[1:])}")
        logger.info("+----------")

        # Wait asynchronously for the job to finish
        exit_code = await self._wait_for_process()

        await self.stop_server()
        return exit_code

    async def _wait_for_process(self) -> int:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._process.join)
        return self._process.exitcode

    async def on_shutdown(self):
        if await self.job_is_alive():
            logger.error("+----------")
            logger.error("| Launched job still alive but shutdown initaited")
            logger.error(f"| Shutting down launched job due to server shutdown [{self._process.pid}]")
            logger.error("+----------")
            self._process.kill()
