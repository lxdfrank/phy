# -*- coding: utf-8 -*-
from __future__ import print_function

"""Simple event system."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import string
import re
from collections import defaultdict
from functools import partial
from inspect import getargspec


#------------------------------------------------------------------------------
# Event system
#------------------------------------------------------------------------------

class EventEmitter(object):
    """Class that emits events and accepts registered callbacks.

    Derive from this class to emit events and let other classes know
    of occurrences of actions and events.

    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._callbacks = defaultdict(list)

    def _get_on_name(self, func):
        """Return `eventname` when the function name is `on_<eventname>()`."""
        r = re.match("^on_(.+)$", func.__name__)
        if r:
            event = r.group(1)
        else:
            raise ValueError("The function name should be "
                             "`on_<eventname>`().")
        return event

    def _create_emitter(self, event):
        """Create a method that emits an event of the same name."""
        if not hasattr(self, event):
            setattr(self, event,
                    lambda *args, **kwargs: self.emit(event, *args, **kwargs))

    def connect(self, func=None, event=None, set_method=False):
        """Register a callback function to a given event.

        To register a callback function to the `spam` event, where `obj` is
        an instance of a class deriving from `EventEmitter`:

        ```python
        @obj.connect
        def on_spam(arg1, arg2):
            pass
        ```

        This is called when `obj.emit('spam', arg1, arg2)` is called.

        Several callback functions can be registered for a given event.

        The registration order is conserved and may matter in applications.

        """
        if func is None:
            return partial(self.connect, set_method=set_method)

        # Get the event name from the function.
        if event is None:
            event = self._get_on_name(func)

        # We register the callback function.
        self._callbacks[event].append(func)

        # A new method self.event() emitting the event is created.
        if set_method:
            self._create_emitter(event)

        return func

    def unconnect(self, *funcs):
        """Unconnect specified callback functions."""
        for func in funcs:
            for callbacks in self._callbacks.values():
                if func in callbacks:
                    callbacks.remove(func)

    def emit(self, event, *args, **kwargs):
        """Call all callback functions registered with an event.

        Any positional and keyword arguments can be passed here, and they will
        be fowarded to the callback functions.

        Return the list of callback return results.

        """
        res = []
        for callback in self._callbacks.get(event, []):
            argspec = getargspec(callback)
            if not argspec.keywords:
                # Only keep the kwargs that are part of the callback's
                # arg spec, unless the callback accepts `**kwargs`.
                kwargs = {n: v for n, v in kwargs.items()
                          if n in argspec.args}
            res.append(callback(*args, **kwargs))
        return res


#------------------------------------------------------------------------------
# Progress reporter
#------------------------------------------------------------------------------

class PartialFormatter(string.Formatter):
    """Prevent KeyError when a format parameter is absent."""
    def get_field(self, field_name, args, kwargs):
        try:
            return super(PartialFormatter, self).get_field(field_name,
                                                           args,
                                                           kwargs)
        except (KeyError, AttributeError):
            return None, field_name

    def format_field(self, value, spec):
        if value is None:
            return '?'
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            return '?'


def _default_on_progress(message, value, value_max, **kwargs):
    if value_max == 0:
        return
    if value < value_max:
        progress = 100 * value / float(value_max)
        fmt = PartialFormatter()
        print(fmt.format(message, progress=progress, **kwargs), end='\r')


def _default_on_complete(message, **kwargs):
    # Override the initializing message and clear the terminal
    # line.
    fmt = PartialFormatter()
    print(fmt.format(message + '\033[K', **kwargs), end='\n')


class ProgressReporter(EventEmitter):
    """A class that reports progress done.

    Emits
    -----

    * `progress(value, value_max)`
    * `complete()`

    """
    def __init__(self):
        super(ProgressReporter, self).__init__()
        self._value = 0
        self._value_max = 0
        self._has_completed = False

    def set_progress_message(self, message):
        """Set a progress message.

        The string needs to contain `{progress}`.

        """

        @self.connect
        def on_progress(value, value_max, **kwargs):
            _default_on_progress(message, value, value_max, **kwargs)

    def set_complete_message(self, message):
        """Set a complete message."""

        @self.connect
        def on_complete(**kwargs):
            _default_on_complete(message, **kwargs)

    def _set_value(self, value, **kwargs):
        if value < self._value_max:
            self._has_completed = False
        self._value = value
        self.emit('progress', self._value, self._value_max, **kwargs)
        if not self._has_completed and self._value >= self._value_max:
            self.emit('complete', **kwargs)
            self._has_completed = True

    def increment(self, **kwargs):
        self._set_value(self._value + 1, **kwargs)

    def reset(self, value_max=None):
        super(ProgressReporter, self).reset()
        self._value = 0
        if value_max is not None:
            self._value_max = value_max

    @property
    def value(self):
        """Current value (integer)."""
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)

    @property
    def value_max(self):
        """Maximum value."""
        return self._value_max

    @value_max.setter
    def value_max(self, value_max):
        if value_max > self._value_max:
            self._has_completed = False
        self._value_max = value_max

    def is_complete(self):
        """Return wheter the task has completed."""
        return self._value >= self._value_max

    def set_complete(self, **kwargs):
        """Set the task as complete."""
        self._set_value(self.value_max, **kwargs)

    @property
    def progress(self):
        """Return the current progress."""
        return self._value / float(self._value_max)
