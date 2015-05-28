import datetime
from weakref import WeakKeyDictionary

import logbook
from nameko.extensions import DependencyProvider


class LoggingDependency(DependencyProvider):

    def __init__(self, interval='s'):
        self.timestamps = WeakKeyDictionary()
        self.interval = interval

    def worker_setup(self, worker_ctx):
        self.timestamps[worker_ctx] = datetime.datetime.now()
        service_name = worker_ctx.service_name
        method_name = worker_ctx.entrypoint.method_name
        logbook.debug(('Worker {service}.{method} starting'
                       .format(service=service_name, method=method_name)))

    def worker_result(self, worker_ctx, result=None, exc_info=None):
        service_name = worker_ctx.service_name
        method_name = worker_ctx.entrypoint.method_name
        status = 'completed' if exc_info is None else 'errored'
        now = datetime.datetime.now()
        worker_started = self.timestamps.pop(worker_ctx)
        if self.interval == 's':
            duration = (now - worker_started).seconds
        elif self.interval == 'ms':
            duration = (now - worker_started).microseconds
        msg = ('Worker {service}.{method} {status} after {duration}{interval}'
               .format(service=service_name, method=method_name, status=status,
                       duration=duration, interval=self.interval))
        logbook.debug(msg)
