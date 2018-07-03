import time
import os
import signal
from datetime import datetime, timezone
from email.utils import formatdate
from threading import Thread
from ..responses import update_current_time
from ..protocol import ConnectionStatus, update_current_time as update_time_protocol


class Reaper(Thread):
    def __init__(self, app):
        super().__init__()

        self.app = app

        # Early bindings
        self.connections: set = self.app.connections

        # How long we allow a connection being idle.
        self.keep_alive_timeout: int = self.app.server_limits.keep_alive_timeout

        # In case the worker is stuck for some crazy reason (sync calls, expensive CPU ops) we gonna kill it.
        self.worker_timeout: int = self.app.server_limits.worker_timeout

        # Flag to stop this thread.
        self.has_to_work: bool = True

    @staticmethod
    async def kill_connections(connections: list):
        for connection in connections:
            connection.transport.clean_up()

    def check_if_worker_is_stuck(self):
        """

        :return:
        """
        current_time = time.time()
        for connection in self.app.connections.copy():
            conditions = (
                connection.get_status() == ConnectionStatus.PROCESSING_REQUEST,
                current_time - connection.get_last_task_time() >= self.worker_timeout
            )
            if all(conditions):
                # ###############
                # Seppuku #######
                # # # # # # # # #
                os.kill(os.getpid(), signal.SIGKILL)

    def kill_idle_connections(self):
        """

        :return:
        """
        now = time.time()
        for connection in self.connections.copy():
            if connection.get_status() == ConnectionStatus.PENDING and \
                    (now - connection.get_last_task_time() > self.keep_alive_timeout):
                connection.stop()

    def run(self):
        """

        :return:
        """
        counter = 0
        while self.has_to_work:
            counter += 1

            # Removing the microseconds because this time is cached and it could trick the user into believing
            # that two requests were processed at exactly the same time because of the cached time.
            now = datetime.now(timezone.utc).replace(microsecond=0).astimezone()
            self.app.current_time = now.isoformat()
            update_current_time(formatdate(timeval=now.timestamp(), localtime=False, usegmt=True))
            update_time_protocol()

            if self.keep_alive_timeout > 0:
                if counter % self.keep_alive_timeout == 0:
                    self.kill_idle_connections()

            if counter % self.worker_timeout == 0:
                self.check_if_worker_is_stuck()

            time.sleep(1)
