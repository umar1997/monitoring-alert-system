import os
import time

def calculate_time(start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"*********Elapsed Time: {int(hours)} Hours, {int(minutes)} Minutes, {int(seconds)} Seconds*********")


# Remove PDF Files
def remove_pdf_file(file_pdf_path):        
    if os.path.exists(file_pdf_path):
        try:
            os.chmod(file_pdf_path, 0o777)
            os.remove(file_pdf_path)
        except Exception as e:
            print(f"Exception: {e}")


class TimerContext:
    def __init__(self, timer: "Timer", name: str):
        self.timer = timer
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        PAD=30
        for k, v in self.timer.elapsed_times.items():
            print(f"{k:<{PAD}}: {v/60:.2f} minutes , {v:.2f} seconds")

        if any([exc_type, exc_val, exc_tb]):

            raise exc_val
        self.timer.elapsed_times[self.name] = time.time() - self.start_time


class Timer:
    """
    A simple timer that tracks the elapsed time of each context.

    Examples
    --------
    >>> t = Timer()
    >>> with t("test"):
    ...     time.sleep(1)
    >>> assert int(t.elapsed_times.get("test", 0)) >= 1, "The elapsed time should be 1 second."
    """

    def __init__(self):
        self.elapsed_times = {}

    def __call__(self, name: str) -> TimerContext:
        """
        Create a context with the given name.

        Parameters
        ----------
        name: str
            The name of the context.

        Returns
        -------
        TimerContext
            The context.

        Examples
        --------
        >>> t = Timer()
        >>> with t("test"):
        ...     time.sleep(1)
        >>> assert int(t.elapsed_times.get("test", 0)) == 1, "The elapsed time should be 1 second."
        >>> with t("test2"):
        ...     time.sleep(2)
        >>> assert int(t.elapsed_times.get("test2", 0)) == 2, "The elapsed time should be 2 seconds."
        """
        return TimerContext(self, name)