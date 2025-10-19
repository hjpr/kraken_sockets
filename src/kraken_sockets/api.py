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

from schema.requests import (
    BalancesSubscriptionRequest,
    BookSubscriptionRequest,
    ExecutionSubscriptionRequest,
    InstrumentsSubscriptionRequest,
    OHLCSubscriptionRequest,
    OrdersSubscriptionRequest,
    PingRequest,
    SubscriptionRequest
)
from schema.responses import (

    # Admin responses
    Response,
    HeartbeatResponse,
    PingResponse,
    StatusResponse,

    # Snapshot responses
    SnapshotResponse,
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
    UpdateResponse,
    BookUpdateResponse,
    InstrumentsUpdateResponse,
    OHLCUpdateResponse,
    OrderUpdateResponse,
    TickerUpdateResponse,
    TradesUpdateResponse
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
    
    _message_queue: asyncio.Queue
    _user_handler: Callable | None
    _user_log_handler: Callable | None
    _user_triggers: Dict[Response, Callable]
    _user_tasks: List[Callable]

    def __init__(self):
        self.available_channels: set = set({})
        self._message_queue = asyncio.Queue()
        self._user_triggers: Dict[Response, Callable] = {}
        self._user_handler: Callable | None = None
        self._user_log_handler: Callable | None = None
        self._user_tasks: List[Callable] = []
        self.websocket_public: websockets.ClientConnection | None = None
        self.websocket_private: websockets.ClientConnection | None = None

    async def _listen(self, socket: websockets.ClientConnection, name: str):
        """Generic listener loop for a websocket connection."""
        while True:
            try:
                message = await socket.recv()
                await self._message_queue.put(message)
            except websockets.exceptions.ConnectionClosed:
                print(f"Connection to {name} websocket closed.")
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
            if method == "subscribe":
                channel = message.get("result", {}).get("channel")
            else:
                channel = message.get("channel")
            message_type = message.get("type")

            try:
                if channel == "status":
                    response = StatusResponse(message)

                if channel == "heartbeat":
                    response = HeartbeatResponse()

                if method == "pong":
                    response = PingResponse(message)

                if method == "subscribe":
                    response = SubscriptionResponse(message)
                    self.available_channels.add(response.channel)

                if method == "unsubscribe":
                    response = UnsubscribeResponse(message)
                    self.available_channels.discard(response.channel)

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
                            response = TradesSnapshotResponse
                        case "ohlc":
                            response = OHLCSnapshotResponse(message)

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
                            
                response_type = type(response)
                if response_type in self._user_triggers:
                    func = self._user_triggers[response_type]
                    await func(response)

            except Exception as e:
                print(f"Error processing message in queue: {e}")
            finally:
                self._message_queue.task_done()

    async def _create_public_websocket(self) -> None:
        try:
            self.websocket_public = await websockets.connect(KRAKEN_WSS_PUBLIC_URI)
        except websockets.exceptions.ConnectionClosed:
            print("Lost connection to public websocket. Retrying in 5 seconds...")
            asyncio.sleep(5)
            self._create_public_websocket()

    async def _create_private_websocket(self) -> None:
        try:
            self.websocket_private = await websockets.connect(KRAKEN_WSS_AUTH_URI)
        except websockets.exceptions.ConnectionClosed:
            print("Lost connection to private websocket. Retrying in 5 seconds...")
            asyncio.sleep(5)
            self._create_private_websocket()

    def log(self, log: str, priority: str) -> None:
        """Uses decorated log hander for logging, otherwise defaults to root logger."""
        if self._user_log_handler:
            self._user_log_handler(log)
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

    def trigger(self, trigger: Response) -> Callable:
        if not inspect.isclass(trigger) or not issubclass(trigger, Response):
            raise ValueError("Trigger doesn't match a known Response schema.")
        def decorator(func) -> Callable:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("Triggers must be coroutines.")
            if trigger not in self._user_triggers:
                self._user_triggers[trigger] = func
            else:
                raise ValueError("Can't register two functions for one trigger.")
        return decorator

    def user_logger(self, func: Callable) -> Callable:
        """
        A decorator to register a function as a log hander so user can output logs
        using their own logging system

        Returns:
            func (function): Runs the decorated function and passes the log string
                to the wrapped function.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User log handler must be coroutine.")
        self._log_handler = func
        return func

    def user_message_handler(self, func: Callable) -> Callable:
        """
        A decorator to register an asynchronous function as the message handler.
        
        The decorated function will be called with each message received from
        the WebSocket connections.

        Returns:
            func (function): Runs the decorated function and passes two arguments
                through. The first arg is the string parsed into a dict, and the second
                arg is a schema-formatted response class.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User message handler must be coroutine.")
        if self._user_handler:
            raise ValueError("Can't register two message handlers at a time.")
        self._user_handler = func
        return func
    
    def user_task(self, func: Callable) -> None:
        """
        A decorator to register a user function into the async loop.

        The decorated function will ent
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("User task must be coroutine.")
        if func not in self._user_tasks:
            self._user_tasks.append(func)
            self.log(f"Registered {func.__name__} into async loop.")

    async def subscribe(self, message: List[SubscriptionRequest]) -> None:
        """Sends subscription messages to both public and private endpoints. Use proper schema to ensure proper routing."""

        for sub_msg in message:
            if not isinstance(sub_msg, SubscriptionRequest):
                print("Invalid subscription schema used. Utilize the schema classes found in module per endpoint.")
            if sub_msg.public:
                await self.websocket_public.send(json.dumps(sub_msg))
            elif not sub_msg.public:
                await self.websocket_private.send(json.dumps(sub_msg))

    async def run(self, subscriptions: List[SubscriptionRequest] = []):
        """Connects to the websockets, subscribes to channels, and starts the message handling loop."""

        if not self._user_log_handler:
            self.log("No user log handler registered. Use @<instance>.user_logger to register custom log hander. Defaulting to backup logs", "warning")

        if not self._user_handler:
            self.log("No handler registered. Use @<instance>.message_handler to register custom handler.", "warning")

        if not self._user_tasks:
            self.log("No user tasks registered. Use @<instance>.user_task to register a task to run in the async loop.", "warning")

        tasks = []

        public_subscriptions = [sub_msg for sub_msg in subscriptions if sub_msg.public]
        private_subscriptions = [sub_msg for sub_msg in subscriptions if not sub_msg.public]

        # Connect to public endpoint if needed
        if public_subscriptions:
            await self._create_public_websocket()

            # Send subscription messages
            for sub_msg in public_subscriptions:
                await self.websocket_public.send(sub_msg.serialize())

            # Create our public websocket listener
            tasks.append(asyncio.create_task(self._listen(self.websocket_public, "public")))

        # Connect to private endpoint if needed
        if private_subscriptions:
            kraken_auth = KrakenAuth()
            if not kraken_auth.token:
                raise ValueError("Cannot subscribe to private channels. KRAKEN_REST_API keys are missing or invalid.")
            await self._create_private_websocket()

            # Add the token to each private subscription message and send subscription messages
            for sub_msg in private_subscriptions:
                sub_msg.params["token"] = kraken_auth.token
                await self.websocket_private.send(sub_msg.serialize())

            # Create our private websocket listener
            tasks.append(asyncio.create_task(self._listen(self.websocket_private, "private")))

        # Add in user tasks from decorators
        for task in self._user_tasks:
            tasks.append(asyncio.create_task(task))

        # Start the central message processor
        processing_task = asyncio.create_task(self._process_messages())
        tasks.append(processing_task)

        print("Kraken WebSocket client running. Press Ctrl+C to stop.")
        await asyncio.gather(*tasks)