from .definitions import *
from . import cprotocol

locals()['Connection'] = cprotocol.Connection
locals()['update_current_time'] = cprotocol.update_current_time
