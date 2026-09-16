"""Шина событий и одиночный сигнал. Только callable, никакой сериализации."""


class EventBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, event_type, callback):
        self._subs.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type, callback):
        if event_type in self._subs and callback in self._subs[event_type]:
            self._subs[event_type].remove(callback)

    def emit(self, event_type, **data):
        for cb in list(self._subs.get(event_type, [])):
            cb(**data)


class Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, cb):
        self._callbacks.append(cb)

    def disconnect(self, cb):
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    def emit(self, *args, **kwargs):
        for cb in list(self._callbacks):
            cb(*args, **kwargs)
