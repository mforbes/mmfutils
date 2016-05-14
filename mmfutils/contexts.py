"""Various useful contexts.

with Interrupts() as interrupted:
    while not interrupted:
        do stuff


"""
import signal
from threading import RLock


class Interrupt(object):
    """Suspend the various signals during the execution block.

    >>> import os, signal, time

    This loop will get interrupted in the middle so that m and n will not be
    the same.

    >>> def f(n, interrupted=False):
    ...     done = False
    ...     while not done and not interrupted:
    ...         n[0] += 1
    ...         if n[0] == 5:
    ...             # Simulate user interrupt
    ...             os.kill(os.getpid(), signal.SIGINT)
    ...             time.sleep(0.1)
    ...         n[1] += 1
    ...         done = n[0] >= 10

    >>> n = [0, 0]
    >>> try:
    ...     f(n)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
    >>> n
    [5, 4]

    Now we protect the loop from interrupts.
    >>> n = [0, 0]
    >>> try:
    ...     with Interrupt() as interrupted:
    ...         f(n)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
    >>> n
    [10, 10]

    If `f()` is slow, we might want to interrupt it at safe times.  This is
    what the `interrupted` flag is for:

    >>> n = [0, 0]
    >>> try:
    ...     with Interrupt() as interrupted:
    ...         f(n, interrupted)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
    >>> n
    [5, 5]
    """
    _interrupts = set()
    _signals = set((signal.SIGINT, signal.SIGTERM))
    _signal_handlers = {}  # Dictionary of original handlers
    _signals_raised = []

    # Lock should be re-entrant (I think) since a signal might be sent during
    # operation of one of the functions.
    _lock = RLock()

    @classmethod
    def catch_signals(cls, signals=None):
        """Set signals and register the signal handler if there are any
        interrupt instances."""
        with cls._lock:
            if signals:
                cls._signals = set(signals)
                cls._reset_handlers()

            if cls._interrupts:
                # Only set the handlers if there are interrupt instances
                cls._set_handlers()

    @classmethod
    def _reset_handlers(cls):
        with cls._lock:
            for _sig in list(cls._signal_handlers):
                signal.signal(_sig, cls._signal_handlers.pop(_sig))

    @classmethod
    def _set_handlers(cls):
        with cls._lock:
            cls._reset_handlers()
            for _sig in cls._signals:
                cls._signal_handlers[_sig] = signal.signal(
                    _sig, cls.handle_signal)
        
    @classmethod
    def handle_signal(cls, signum, frame):
        with cls._lock:
            cls._signals_raised.append((signum, frame))

    def __init__(self):
        Interrupt._interrupts.add(self)
        self.catch_signals()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._interrupts.remove(self)
            if not self._interrupts:
                self._reset_handlers()
                if exc_type is None and self:
                    # Only raise an exception if all the interrupts have been
                    # cleared, otherwise we might still be in a protected
                    # context somewhere.
                    while self._signals_raised:
                        # Clear previous signals
                        self._signals_raised.pop()
                    raise KeyboardInterrupt()

    @classmethod
    def __nonzero__(cls):
        with cls._lock:
            return bool(cls._signals_raised)