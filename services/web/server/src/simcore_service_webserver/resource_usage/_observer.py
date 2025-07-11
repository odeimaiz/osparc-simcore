"""Handlers to events registered in servicelib.observer.event_registry"""

import logging

from aiohttp import web
from models_library.products import ProductName
from models_library.users import UserID
from servicelib.aiohttp.observer import (
    registed_observers_report,
    register_observer,
    setup_observer_registry,
)
from servicelib.utils import logged_gather

from ..notifications import wallet_osparc_credits
from ..wallets import api as wallets_service

_logger = logging.getLogger(__name__)


async def _on_user_disconnected(
    user_id: UserID,
    client_session_id: str,
    app: web.Application,
    product_name: ProductName,
) -> None:
    assert product_name  # nosec
    assert client_session_id  # nosec

    # Get all user wallets and unsubscribe
    user_wallet = await wallets_service.list_wallets_for_user(
        app, user_id=user_id, product_name=product_name
    )
    disconnect_tasks = [
        wallet_osparc_credits.unsubscribe(app, wallet.wallet_id)
        for wallet in user_wallet
    ]
    await logged_gather(*disconnect_tasks)


async def _on_user_connected(
    user_id: UserID,
    app: web.Application,
    product_name: ProductName,
    client_session_id: str,
) -> None:
    assert client_session_id  # nosec
    # Get all user wallets and subscribe
    user_wallet = await wallets_service.list_wallets_for_user(
        app, user_id=user_id, product_name=product_name
    )
    _logger.debug("Connecting user %s to wallets %s", f"{user_id}", f"{user_wallet}")
    connect_tasks = [
        wallet_osparc_credits.subscribe(app, wallet.wallet_id) for wallet in user_wallet
    ]
    await logged_gather(*connect_tasks)


def setup_resource_usage_observer_events(app: web.Application) -> None:
    # add
    setup_observer_registry(app)

    register_observer(app, _on_user_connected, event="SIGNAL_USER_CONNECTED")
    register_observer(app, _on_user_disconnected, event="SIGNAL_USER_DISCONNECTED")

    _logger.info(
        "App registered events (at this point):\n%s", registed_observers_report(app)
    )
