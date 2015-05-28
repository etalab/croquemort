import logbook

from nameko.events import EventDispatcher
from nameko.timer import timer

from logger import LoggingDependency
from storages import RedisStorage

log = logbook.debug


class TimerService(object):
    name = 'timer'
    dispatch = EventDispatcher()
    storage = RedisStorage()
    logger = LoggingDependency()

    @timer(60*60)
    def check_hourly(self):
        log('Checking hourly resources')
        for url in self.storage.get_frequency_urls(frequency='hourly'):
            self.dispatch('url_to_check', (url, None, None))

    @timer(60*60*24)
    def check_daily(self):
        log('Checking daily resources')
        for url in self.storage.get_frequency_urls(frequency='daily'):
            self.dispatch('url_to_check', (url, None, None))

    @timer(60*60*24*30)
    def check_monthly(self):
        log('Checking monthly resources')
        for url in self.storage.get_frequency_urls(frequency='monthly'):
            self.dispatch('url_to_check', (url, None, None))
