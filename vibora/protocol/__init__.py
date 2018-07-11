from typing import TYPE_CHECKING
from .cprotocol import *  # noqa


class ConnectionStatus:
    PENDING = 1
    PROCESSING_REQUEST = 2
    WEBSOCKET = 3


if TYPE_CHECKING:
    from .hints import *  # noqa
