import threading
import typing
import time


class Necromancer(threading.Thread):
    def __init__(self, workers: list, spawn_function: typing.Callable, interval=5):
        super().__init__()
        self.workers = workers
        self.spawn_function = spawn_function
        self.interval = interval

    def run(self):
        while self.workers:
            time.sleep(self.interval)
            workers_alive = []
            for worker in self.workers:
                if not worker.is_alive():
                    worker = self.spawn_function()
                    worker.start()
                    workers_alive.append(worker)
                else:
                    workers_alive.append(worker)
            self.workers = workers_alive
