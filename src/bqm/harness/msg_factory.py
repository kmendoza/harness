import datetime as dt
from multiprocessing import Process
from typing import Any

import psutil
from fastapi import Request
from fastapi.responses import JSONResponse

from bqm.harness.commands import Command


class MessageFactory:

    def mk_hb_response(rqst: Request, process: Process = None, status: bool = True) -> JSONResponse:

        ps_proc = psutil.Process(process.pid)

        service = {}
        process_state = {
            "pid": ps_proc.pid,
            "name": ps_proc.name(),
            "status": ps_proc.status(),
            "cpu-pct": ps_proc.cpu_percent(interval=0.25),
            "mem-rss-mb": ps_proc.memory_info().rss / (1024 * 1024),
            "threads": ps_proc.num_threads(),
            "open-files": ps_proc.open_files(),
            "created": ps_proc.create_time(),
        }
        return JSONResponse(
            content={
                "status": status,
                "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                "service": service,
                "process": process_state,
            }
        )

    def mk_cmd_response(rqst: Request, cmd: Command, process: Process = None) -> JSONResponse:
        return JSONResponse(
            content={
                "status": "SENT",
                "command": cmd,
                "target-process": process.pid,
                "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            }
        )

    def mk_cmd_err_response(rqst: Request, cmd: Command, error: str, process: Process = None, status_code: int = 500) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "command": cmd,
                "status": "ERROR",
                "error": error,
                "target-process": process.pid,
                "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            },
        )

    def mk_status_response(rqst: Request, status: dict[str, Any], process: Process = None) -> JSONResponse:
        return JSONResponse(
            content={
                "process-status": status if status else {},
                "target-process": process.pid,
                "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            },
        )
