import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from uvicorn import Config, Server

from bqm.harness.conf.config_parser import ConfigParser

logger = logging.getLogger(__name__)


class ServiceInterface(ABC):
    def __init__(self, config: dict[str, Any]):
        logger.setLevel(logging.INFO)
        self._config = ConfigParser(config)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self.on_startup()
            try:
                yield
            except Exception as e:
                logger.error(f"ERROR on lifspan yield : {e}")
            finally:
                await self.on_shutdown()

        self._app = FastAPI(lifespan=lifespan)
        self._register_exception_handlers()
        self._register_routes()

    def _start_server(self):
        logger.info("Starting FastAPI server")
        self._config = Config(
            app=self._app,
            host=self._config.get_iface(),
            port=self._config.get_port(),
            log_level="info",
            loop="asyncio",
        )
        self._server = Server(self._config)
        self._server_task = asyncio.create_task(self._server.serve())
        logger.info("FastAPI server started")

    def _register_routes(self):
        self._app.get("/hb")(self._hb)
        self._app.get("/start")(self._start)
        self._app.get("/stop")(self._stop)
        self._app.get("/pause")(self._pause)
        self._app.get("/resume")(self._resume)
        self._app.get("/kill")(self._kill)
        self._app.get("/status")(self._status)
        self._app.post("/data")(self._data)
        logger.info(f"registered routes: {self._app.routes}")

    def _register_exception_handlers(self):
        self._app.add_exception_handler(HTTPException, self._handle_http_exception)
        self._app.add_exception_handler(Exception, self._handle_service_exception)

    @abstractmethod
    async def _hb(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _start(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _stop(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _pause(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _resume(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _data(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _status(self, req: Request) -> JSONResponse: ...

    @abstractmethod
    async def _kill(self, req: Request) -> JSONResponse: ...

    async def _handle_http_exception(self, req: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Route not found: {req.url.path}"},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    async def _handle_service_exception(self, req: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": f"An internal error occurred: {exc}"},
        )

    async def stop_server(self):
        logger.info("Stopping server...")
        self._server.should_exit = True
        await self._server_task
        logger.info("Server stopped.")

    # ----------------
    # public interface
    # ----------------
    async def on_startup(self):
        pass

    async def on_shutdown(self):
        pass


# # Entry point
# if __name__ == "__main__":
#     asyncio.run(RunnerImpl(config).main(1, 2, 3))
