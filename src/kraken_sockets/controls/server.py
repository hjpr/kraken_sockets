
import uvicorn

from fastapi import FastAPI

from kraken_sockets.controls.routes import build_router


class ControlServer:
    """
    Manages the local FastAPI control server that runs inside the main asyncio event loop
    alongside the WebSocket listener tasks.

    Exposes HTTP endpoints that the LLM (or any caller) can use to trigger subscribe,
    unsubscribe, and trading actions without restarting the loop. Commands received over
    HTTP are pushed onto KrakenWebSocketAPI's command_queue and processed asynchronously.

    Args:
        kraken: The running KrakenWebSocketAPI instance. Passed to all route handlers so
            they can enqueue commands and read connection state.
        host (str): Host address to bind the server to. Defaults to '127.0.0.1'.
        port (int): Port to bind the server to. Defaults to 8000.
    """

    def __init__(self, kraken, host: str = "127.0.0.1", port: int = 8000):
        self.app = FastAPI(title="Kraken Sockets Control API")
        self.app.include_router(build_router(kraken))
        self._server = uvicorn.Server(
            uvicorn.Config(
                self.app,
                host=host,
                port=port,
                log_level="warning",
                access_log=False,
            )
        )

    async def serve(self):
        """Coroutine passed into asyncio.gather alongside the WebSocket listener tasks."""
        await self._server.serve()
