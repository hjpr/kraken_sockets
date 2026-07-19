import asyncio
import base64
import hashlib
import hmac
import inspect
import json
import os
import requests
import time
import urllib
import websockets

from dotenv import load_dotenv
from loguru import logger
from typing import Callable, Dict, List

from kraken_sockets.analytics import IndicatorEngine
from kraken_sockets.controls import ControlServer
from kraken_sockets.schema.requests import (
    BalancesSubscriptionRequest,
    BookSubscriptionRequest,
    ExecutionSubscriptionRequest,
    InstrumentsSubscriptionRequest,
    OHLCSubscriptionRequest,
    OrdersSubscriptionRequest,
    PingRequest,
    SubscriptionRequest,
    TradingRequest,
    UnsubscribeRequest,
)
from kraken_sockets.schema.responses import (

    # Admin responses
    Response,
    HeartbeatResponse,
    PingResponse,
    StatusResponse,

    # Trading responses
    AddOrderResponse,
    AmendOrderResponse,
    BatchAddResponse,
    BatchCancelResponse,
    CancelAllOrdersAfterResponse,
    CancelAllResponse,
    CancelOrderResponse,
    EditOrderResponse,

    # Snapshot responses
    BookSnapshotResponse,
    InstrumentsSnapshotResponse,
    OHLCSnapshotResponse,
    OrderSnapshotResponse,
    TickerSnapshotResponse,
    TradesSnapshotResponse,

    # Subscription responses
    SubscriptionResponse,
    UnsubscribeResponse,

    # Update responses
    BookUpdateResponse,
    InstrumentsUpdateResponse,
    OHLCUpdateResponse,
    OrderUpdateResponse,
    TickerUpdateResponse,
    TradesUpdateResponse,

    # User data responses
    BalancesSnapshotResponse,
    BalancesUpdateResponse,
    ExecutionsSnapshotResponse,
    ExecutionsUpdateResponse
)

load_dotenv()

KRAKEN_REST_URL = "https://api.kraken.com"
KRAKEN_REST_API_KEY = os.getenv("KRAKEN_REST_API_KEY")
KRAKEN_REST_API_PRIVATE_KEY = os.getenv("KRAKEN_REST_API_PRIVATE_KEY")

KRAKEN_WSS_PUBLIC_URI = "wss://ws.kraken.com/v2"
KRAKEN_WSS_AUTH_URI = "wss://ws-auth.kraken.com/v2"
KRAKEN_TOKEN_PATH = "/0/private/GetWebSocketsToken"


class KrakenAuth:
    """Utility class for generating and retrieving token for connections to Kraken WS API."""

    token: str

    def __init__(self):
        if KRAKEN_REST_API_KEY and KRAKEN_REST_API_PRIVATE_KEY:
            self.token = self.get_websockets_token()
        else:
            self.token = ""

    @staticmethod
    def get_kraken_signature(urlpath, data, secret):
        """Generates the signature required for private API calls."""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    def get_websockets_token(self) -> str:
        """Fetches a WebSocket authentication token from the Kraken REST API."""
        nonce = str(int(time.time() * 1000))
        data = {"nonce": nonce}
        headers = {
            "API-Key": KRAKEN_REST_API_KEY,
            "API-Sign": self.get_kraken_signature(KRAKEN_TOKEN_PATH, data, KRAKEN_REST_API_PRIVATE_KEY)
        }
        try:
            res = requests.post(f"{KRAKEN_REST_URL}{KRAKEN_TOKEN_PATH}", headers=headers, data=data)
            res.raise_for_status()
            res_data = res.json()
            if res_data.get('error'):
                raise Exception(f"API Error: {res_data['error']}")
            return res_data['result']['token']
        except requests.exceptions.RequestException as e:
            print(f"Error fetching WebSocket token: {e}")
            return ""


class KrakenWebSocketAPI:
    """
    Manages WebSocket connections and data streams from Kraken's API.
    
    A user-defined message handler can be registered using the `@message_handler` decorator.
    """
    available_channels: set
    websocket_public: websockets.ClientConnection
    websocket_private: websockets.ClientConnection

    _token: str
    _message_queue: asyncio.Queue
    command_queue: asyncio.Queue
    _user_handler: Callable | None
    _user_log_handler: Callable | None
    _user_triggers: Dict[Response, Callable]
    _user_tasks: List[Callable]

    def __init__(self):
        self.available_channels: set = set({})
        self._token: str = ""
        self._message_queue = asyncio.Queue()
        self.command_queue = asyncio.Queue()
        self._user_triggers: Dict[Response, Callable] = {}
        self._user_handler: Callable | None = None
        self._user_log_handler: Callable | None = None
        self._user_tasks: List[Callable] = []
        self.websocket_public: websockets.ClientConnection | None = None
        self.websocket_private: websockets.ClientConnection | None = None
        self._private_listener_task: asyncio.Task | None = None
        self._observers: List[Callable] = []
        self.analytics: IndicatorEngine | None = None

    async def _listen(self, socket: websockets.ClientConnection, name: str):
        """Generic listener loop for a websocket connection."""
        while True:
            try:
                message = await socket.recv()
                await self._message_queue.put(message)
            except websockets.exceptions.ConnectionClosed:
                self.log(f"Connection to {name} websocket closed.", "warning")
                break

    async def _process_messages(self):
        """
        The consumer task that takes raw message strings from the internal queue, processes
        into respective schema, and passes them to the user-registered handler.
        """
        while True:
            message = await self._message_queue.get()
            message = json.loads(message) if message else {}

            # Retrieve message details to determine how to handle
            method = message.get("method")
            if method in ("subscribe", "unsubscribe"):
                channel = message.get("result", {}).get("channel")
            else:
                channel = message.get("channel")
            message_type = message.get("type")
            response = None

            try:
                if channel == "status":
                    response = StatusResponse(message)

                if channel == "heartbeat":
                    response = HeartbeatResponse()

                if method == "pong":
                    response = PingResponse(message)

                if method == "subscribe":
                    response = SubscriptionResponse(message)
                    symbol = response.result.get("symbol")
                    label = f"'{response.channel}' {symbol}" if symbol else f"'{response.channel}'"
                    if response.success:
                        self.available_channels.add(response.channel)
                        self.log(f"Subscribed to {label}", "info")
                    else:
                        self.log(f"Subscribe request rejected: {response.error}", "warning")

                if method in ("add_order", "amend_order", "edit_order", "cancel_order",
                              "cancel_all", "cancel_all_orders_after", "batch_add", "batch_cancel"):
                    match method:
                        case "add_order":
                            response = AddOrderResponse(message)
                        case "amend_order":
                            response = AmendOrderResponse(message)
                        case "edit_order":
                            response = EditOrderResponse(message)
                        case "cancel_order":
                            response = CancelOrderResponse(message)
                        case "cancel_all":
                            response = CancelAllResponse(message)
                        case "cancel_all_orders_after":
                            response = CancelAllOrdersAfterResponse(message)
                        case "batch_add":
                            response = BatchAddResponse(message)
                        case "batch_cancel":
                            response = BatchCancelResponse(message)
                    if response.success:
                        self.log(f"'{method}' acknowledged by engine.", "info")
                    else:
                        self.log(f"'{method}' rejected by engine: {response.error}", "warning")

                if method == "unsubscribe":
                    response = UnsubscribeResponse(message)
                    symbol = response.result.get("symbol")
                    label = f"'{response.channel}' {symbol}" if symbol else f"'{response.channel}'"
                    if response.success:
                        self.available_channels.discard(response.channel)
                        self.log(f"Unsubscribed from {label}", "info")
                    else:
                        self.log(f"Unsubscribe request rejected: {response.error}", "warning")

                if message_type == "snapshot":
                    match channel:
                        case "book":
                            response = BookSnapshotResponse(message)
                        case "instrument":
                            response = InstrumentsSnapshotResponse(message)
                        case "level3":
                            response = OrderSnapshotResponse(message)
                        case "ticker":
                            response = TickerSnapshotResponse(message)
                        case "trade":
                            response = TradesSnapshotResponse(message)
                        case "ohlc":
                            response = OHLCSnapshotResponse(message)
                        case "executions":
                            response = ExecutionsSnapshotResponse(message)
                        case "balances":
                            response = BalancesSnapshotResponse(message)

                if message_type == "update":
                    match channel:
                        case "book":
                            response = BookUpdateResponse(message)
                        case "instrument":
                            response = InstrumentsUpdateResponse(message)
                        case "level3":
                            response = OrderUpdateResponse(message)
                        case "ticker":
                            response = TickerUpdateResponse(message)
                        case "trade":
                            response = TradesUpdateResponse(message)
                        case "ohlc":
                            response = OHLCUpdateResponse(message)
                        case "executions":
                            response = ExecutionsUpdateResponse(message)
                        case "balances":
                            response = BalancesUpdateResponse(message)
                            
                # Internal observers (e.g. the analytics engine) see every parsed response.
                # Isolated per-observer so one failure can't stall the stream.
                if response is not None:
                    for observer in self._observers:
                        try:
                            await observer(response)
                        except Exception as e:
                            name = getattr(observer, "__qualname__", repr(observer))
                            self.log(f"Error in observer {name}: {e}", "error")

                # Catch-all handler sees every message, parsed or not
                if self._user_handler:
                    await self._user_handler(message, response)

                # Fire the most specific registered trigger for this response type
                if response is not None:
                    for response_class in type(response).__mro__:
                        if response_class in self._user_triggers:
                            await self._user_triggers[response_class](response)
                            break

            except Exception as e:
                self.log(f"Error processing message in queue: {e}", "error")
            finally:
                self._message_queue.task_done()

    async def _process_commands(self):
        """
        Drains the command queue and routes each outbound request to the correct
        websocket connection. Public requests go to websocket_public, private requests
        go to websocket_private. Commands are enqueued by control server route handlers.
        """
        while True:
            command = await self.command_queue.get()
            try:
                if isinstance(command, (SubscriptionRequest, UnsubscribeRequest)):
                    if command.public:
                        if self.websocket_public:
                            await self.websocket_public.send(command.serialize())
                        else:
                            self.log("Cannot send command: public websocket is not connected.", "warning")
                    else:
                        if await self._ensure_private_connection():
                            command.params["token"] = self._token
                            await self.websocket_private.send(command.serialize())
                        else:
                            self.log("Cannot send private command: KRAKEN_REST_API keys are missing or invalid.", "warning")
                elif isinstance(command, TradingRequest):
                    if await self._ensure_private_connection():
                        command.params["token"] = self._token
                        await self.websocket_private.send(command.serialize())
                    else:
                        self.log("Cannot send trading command: KRAKEN_REST_API keys are missing or invalid.", "warning")
            except Exception as e:
                self.log(f"Error sending command: {e}", "error")
            finally:
                self.command_queue.task_done()

    async def _create_public_websocket(self) -> None:
        try:
            self.websocket_public = await websockets.connect(KRAKEN_WSS_PUBLIC_URI)
        except (OSError, websockets.exceptions.WebSocketException):
            self.log("Failed to connect to public websocket. Retrying in 5 seconds...", "warning")
            await asyncio.sleep(5)
            await self._create_public_websocket()

    async def _create_private_websocket(self) -> None:
        try:
            self.websocket_private = await websockets.connect(KRAKEN_WSS_AUTH_URI)
        except (OSError, websockets.exceptions.WebSocketException):
            self.log("Failed to connect to private websocket. Retrying in 5 seconds...", "warning")
            await asyncio.sleep(5)
            await self._create_private_websocket()

    async def _ensure_private_connection(self) -> bool:
        """
        Authenticates and connects the private websocket on demand, starting its
        listener task. Allows private commands to arrive at runtime (e.g. via the
        control server) even when run() started with no private subscriptions.
        Returns False if API keys are missing or invalid.
        """
        if self.websocket_private:
            return True
        if not self._token:
            kraken_auth = KrakenAuth()
            if not kraken_auth.token:
                return False
            self._token = kraken_auth.token
        await self._create_private_websocket()
        self._private_listener_task = asyncio.create_task(self._listen(self.websocket_private, "private"))
        return True

    def log(self, log: str, priority: str) -> None:
        """Uses decorated log hander for logging, otherwise defaults to root logger."""
        if self._user_log_handler:
            try:
                asyncio.create_task(self._user_log_handler(log, priority))
            except RuntimeError:
                pass
        else:
            match priority:
                case "debug":
                    logger.debug(log)
                case "info":
                    logger.info(log)
                case "warning":
                    logger.warning(log)
                case "error":
                    logger.error(log)
                case "critical":
                    logger.critical(log)

    def trigger(self, trigger: type[Response]) -> Callable:
        """
        A decorator to register an asynchronous function to run each time a specific
        response type is received, e.g. @kraken.trigger(TickerUpdateResponse).

        Dispatch is subclass-aware: a trigger registered on a base class such as
        TradingResponse fires for any of its subclasses. When both a specific and a
        base class trigger match, only the most specific one runs. One function can
        be registered per response type.

        Subscription acks share a single class across channels — register on
        SubscriptionResponse and filter with response.channel inside the function.

        Returns:
            func (function): The decorated coroutine, unchanged. It is called with
                the parsed response instance as its only argument.
        """
        if not inspect.isclass(trigger) or not issubclass(trigger, Response):
            raise ValueError("Trigger doesn't match a known Response schema.")
        def decorator(func) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Triggers must be coroutines.")
            if trigger in self._user_triggers:
                raise ValueError("Can't register two functions for one trigger.")
            self._user_triggers[trigger] = func
            return func
        return decorator

    def user_logger(self, func: Callable) -> Callable:
        """
        A decorator to register a function as a log hander so user can output logs
        using their own logging system.

        Returns:
            func (function): Runs the decorated function and passes two parameters
                through. The first arg is the log string, and the second arg is the
                priority of the log.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User log handler must be coroutine.")
        self._user_log_handler = func
        return func

    def add_observer(self, coro: Callable) -> None:
        """
        Registers an internal observer coroutine called with every parsed response,
        before user triggers fire. Used by components like the IndicatorEngine so
        they never occupy user trigger slots. Multiple observers are allowed.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("Observers must be coroutines.")
        if coro not in self._observers:
            self._observers.append(coro)

    def user_message_handler(self, func: Callable) -> Callable:
        """
        A decorator to register an asynchronous function as a catch-all message handler.

        The decorated function is called with every message received from the WebSocket
        connections, before any trigger fires. Useful for recording the full stream,
        e.g. persisting messages for historical analysis.

        Returns:
            func (function): Runs the decorated function and passes two arguments
                through. The first arg is the raw message parsed into a dict, and the
                second arg is the schema-formatted response instance, or None if the
                message did not match a known schema.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User message handler must be coroutine.")
        if self._user_handler:
            raise ValueError("Can't register two message handlers at a time.")
        self._user_handler = func
        return func
    
    def user_task(self, func: Callable) -> Callable:
        """
        A decorator to register a user coroutine into the async loop.

        The decorated function is started once as a task when run() is called,
        alongside the websocket listeners. Use it for long-running or periodic work
        such as computing rolling indicators — manage your own loop and sleep
        interval inside the function.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User task must be coroutine.")
        if func not in self._user_tasks:
            self._user_tasks.append(func)
            self.log(f"Registered {func.__name__} into async loop.", "info")
        return func

    async def trade(self, request: TradingRequest) -> None:
        """
        Enqueues a trading request (AddOrderRequest, CancelOrderRequest, etc.) for
        sending on the private websocket. The session token is injected automatically
        and the engine acknowledgement fires any matching registered trigger.
        """
        if not isinstance(request, TradingRequest):
            self.log("Invalid trading schema used. Utilize the trading request classes found in module.", "warning")
            return
        await self.command_queue.put(request)

    async def subscribe(self, message: List[SubscriptionRequest]) -> None:
        """Sends subscription messages to both public and private endpoints. Use proper schema to ensure proper routing."""

        for sub_msg in message:
            if not isinstance(sub_msg, SubscriptionRequest):
                self.log("Invalid subscription schema used. Utilize the schema classes found in module per endpoint.", "warning")
            if sub_msg.public:
                await self.websocket_public.send(json.dumps(sub_msg))
            elif not sub_msg.public:
                await self.websocket_private.send(json.dumps(sub_msg))

    async def run(
        self,
        subscriptions: List[SubscriptionRequest] = [],
        controls: bool = False,
        host: str = "127.0.0.1",
        port: int = 8000
        ):
        """Connects to the websockets, subscribes to channels, and starts the message handling loop."""

        if not self._user_log_handler:
            self.log("No user log handler registered. Use @<instance>.user_logger to register custom log hander. Defaulting to backup logs", "info")

        if not self._user_tasks:
            self.log("No user tasks registered. Use @<instance>.user_task to register a task to run in the async loop.", "info")

        if not self._user_handler:
            self.log("No catch-all handler registered. Use @<instance>.user_message_handler to observe every message (optional when using triggers).", "info")

        tasks = []

        public_subscriptions = [sub_msg for sub_msg in subscriptions if sub_msg.public]
        private_subscriptions = [sub_msg for sub_msg in subscriptions if not sub_msg.public]

        # Connect to public endpoint if needed
        if public_subscriptions or controls:
            await self._create_public_websocket()

            # Send subscription messages
            for sub_msg in public_subscriptions:
                await self.websocket_public.send(sub_msg.serialize())

            # Create our public websocket listener
            tasks.append(asyncio.create_task(self._listen(self.websocket_public, "public")))

        # Connect to private endpoint if needed
        if private_subscriptions:
            if not await self._ensure_private_connection():
                raise ValueError("Cannot subscribe to private channels. KRAKEN_REST_API keys are missing or invalid.")

            # Add the token to each private subscription message and send subscription messages
            for sub_msg in private_subscriptions:
                sub_msg.params["token"] = self._token
                await self.websocket_private.send(sub_msg.serialize())

            # Private websocket listener task is created by _ensure_private_connection
            tasks.append(self._private_listener_task)

        # Add in user tasks from decorators
        for task in self._user_tasks:
            tasks.append(asyncio.create_task(task()))

        # Start the central message processor
        tasks.append(asyncio.create_task(self._process_messages()))

        # Start the command queue processor
        tasks.append(asyncio.create_task(self._process_commands()))

        # Optionally start the local control server with the analytics engine attached.
        # Pre-build kraken.analytics with custom windows before run() to override defaults.
        if controls:
            if self.analytics is None:
                self.analytics = IndicatorEngine(self)
            control_server = ControlServer(self, host=host, port=port)
            tasks.append(asyncio.create_task(control_server.serve()))
            self.log(f"Control server running at http://{host}:{port}", "info")

        self.log("Kraken WebSocket client running. Press Ctrl+C to stop.", "info")
        await asyncio.gather(*tasks)