import atexit
import contextlib


def enter_for_process_lifetime[T](
    cm: contextlib.AbstractContextManager[T],
) -> T:
    col = cm.__enter__()

    @atexit.register
    def shutdown():
        cm.__exit__(None, None, None)

    return col
