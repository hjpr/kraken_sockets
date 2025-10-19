
from schema.requests.base_requests import SubscriptionRequest
from typing import Literal, Optional


class BalancesSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to private 'balances' channel which streams client asset
    balances and transactions from the account ledger.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/balances

    Args:
        snapshot (bool): Request a snapshot after subscribing.
        rebased (bool): For viewing xstocks only. If true, display in terms of underlying equity,
            otherwise display in terms of SPV tokens.
        users (str): If 'all', events for master and subaccounts are streamed,
            otherwise only master account events are published. No snapshot is provided.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    snapshot: bool
    rebased: bool
    users: Optional[Literal["all"]]

    def __init__(
        self,
        snapshot = True,
        rebased = True,
        users = None,
        req_id = None
    ):
        super().__init__()
        self.public = False,
        self.method = "subscribe",
        self.params = {
            "channel": "balances",
            "snapshot": snapshot,
        },
        self.req_id = req_id,
        self.rebased = rebased,
        self.users = users             


class ExecutionSubscriptionRequest(SubscriptionRequest):
    """
    Build subscription message to private 'executions' channel which streams order status
    and execution events for the account.

    Docs @ https://docs.kraken.com/api/docs/websocket-v2/executions

    Args:
        snap_trades (bool): If true, the last 50 orders will be included in snapshot.
        snap_orders (bool): If true, open orders will be included in snapshot.
        order_status (bool): If true, all possible status transitions will be sent.
            Otherwise, only open/close transitions will be streamed: 'new', 'filled', 'canceled', 'expired'.
        rebased (bool): For viewing xstocks only. If true, display in terms of underlying equity,
            otherwise display in terms of SPV tokens.
        ratecounter (bool): If true, the rate-limit counter is included in the stream.
        users (str): If 'all', events for master and subaccounts are streamed,
            otherwise only master account events are published. No snapshot is provided.
        req_id (int): Optional client originated request identifier sent as ack in response.
    """

    snap_trades: bool
    snap_orders: bool
    order_status: bool
    rebased: bool
    ratecounter: bool
    users: Optional[Literal["all"]]
    req_id: Optional[int]

    def __init__(
            self,
            snap_trades = False,
            snap_orders = True,
            order_status = True,
            rebased = True,
            ratecounter = True,
            users = None,
            req_id = None
            ):
        super().__init__()
        self.public = False
        self.method = "subscribe",
        self.params = {
            "channel": "executions",
            "snap_trades": snap_trades,
            "snap_orders": snap_orders,
            "order_status": order_status,
            "rebased": rebased,
            "ratecounter": ratecounter,
            "users": users,
        }
        self.req_id = req_id