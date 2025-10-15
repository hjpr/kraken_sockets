import asyncio
import base64
import hashlib
import hmac
import json
import os
import requests
import time
import urllib
import websockets

from dotenv import load_dotenv
from typing import Callable, Coroutine, List
from websockets import ClientConnection

from schema.market_data_subscriptions import MarketDataSubscriptionMessage

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
    def __init__(self):
        self._websocket_public: ClientConnection | None = None
        self._websocket_private: ClientConnection | None = None
        self._message_queue = asyncio.Queue()
        self._user_handler: Callable[[str | bytes], Coroutine] | None = None
        self.available_channels: set = set({})

    def message_handler(self, func: Callable[[str | bytes], Coroutine]) -> Callable:
        """
        A decorator to register an asynchronous function as the message handler.
        
        The decorated function will be called with each message received from
        the WebSocket connections.
        """
        if not asyncio.iscoroutinefunction(func):
                raise TypeError("Message handler must be an async function (coroutine).")
        self._user_handler = func
        return func

    async def _listen(self, socket: ClientConnection, name: str):
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
        The consumer task that takes messages from the internal queue and passes them to the
        user-registered handler.
        """
        while True:
            message = await self._message_queue.get()
            message = json.loads(message)
            try:
                if message:
                    # Add available channels to user accessible list
                    if message.get("method") == "subscribe":
                        self.available_channels.add(message["result"]["channel"])

                    # Remove channels from user accessible list
                    if message.get("method") == "unsubscribe":
                        self.available_channels.discard(message["result"]["channel"])

                    # Execute the user's defined logic for each message
                    await self._user_handler(message)

            except Exception as e:
                print(f"Error in user-defined message handler: {e}")
            finally:
                self._message_queue.task_done()

    async def subscribe(self, message: List[MarketDataSubscriptionMessage]) -> None:
        """Sends subscription messages to both public and private endpoints. Use proper schema to ensure proper routing."""

        for sub_msg in message:
            if not isinstance(sub_msg, MarketDataSubscriptionMessage):
                print("Invalid subscription schema used. Utilize the schema classes found in module per endpoint.")
            if sub_msg.public:
                await self._websocket_public.send(json.dumps(sub_msg))
            elif not sub_msg.public:
                await self._websocket_private.send(json.dumps(sub_msg))

    async def _create_public_websocket(self) -> None:
        try:
            self._websocket_public = await websockets.connect(KRAKEN_WSS_PUBLIC_URI)
        except websockets.exceptions.ConnectionClosed:
            print("Lost connection to public websocket. Retrying in 5 seconds...")
            asyncio.sleep(5)
            self._create_public_websocket()

    async def _create_private_websocket(self) -> None:
        try:
            self._websocket_private = await websockets.connect(KRAKEN_WSS_AUTH_URI)
        except websockets.exceptions.ConnectionClosed:
            print("Lost connection to private websocket. Retrying in 5 seconds...")
            asyncio.sleep(5)
            self._create_private_websocket()

    async def run(self, subscriptions: List[MarketDataSubscriptionMessage] = None):
        """Connects to the websockets, subscribes to channels, and starts the message handling loop."""

        if not self._user_handler:
            raise RuntimeError("No message handler has been registered. Use the @<instance>.message_handler decorator.")

        tasks = []

        public_subscriptions = [sub_msg for sub_msg in subscriptions if sub_msg.public]
        private_subscriptions = [sub_msg for sub_msg in subscriptions if not sub_msg.public]

        # Connect to public endpoint if needed
        if public_subscriptions:

            # Create our public websocket
            await self._create_public_websocket()

            # Send subscription messages
            for sub_msg in public_subscriptions:
                await self._websocket_public.send(sub_msg.serialize())

            # Create our public websocket listener
            tasks.append(asyncio.create_task(self._listen(self._websocket_public, "public")))

        # Connect to private endpoint if needed
        if private_subscriptions:

            # Generate our token
            kraken_auth = KrakenAuth()
            if not kraken_auth.token:
                raise ValueError("Cannot subscribe to private channels. KRAKEN_REST_API keys are missing or invalid.")
            
            # Create our private websocket
            await self._create_private_websocket()

            # Add the token to each private subscription message and send subscription messages
            for sub_msg in private_subscriptions:
                sub_msg.params["token"] = kraken_auth.token
                await self._websocket_private.send(sub_msg.serialize())

            # Create our private websocket listener
            tasks.append(asyncio.create_task(self._listen(self._websocket_private, "private")))

        if not tasks:
            print("No subscriptions provided during initialization. You can manually subscribe to channels using .subscribe()")
            return

        # Start the central message processor
        processing_task = asyncio.create_task(self._process_messages())
        tasks.append(processing_task)

        print("Kraken WebSocket client running. Press Ctrl+C to stop.")
        await asyncio.gather(*tasks)