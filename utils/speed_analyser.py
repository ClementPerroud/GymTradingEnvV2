import time
import threading
import contextvars
from functools import wraps

# A context variable that holds the current active step, allowing nesting.
current_step_var = contextvars.ContextVar("current_step", default=None)


class StepTimer:
    """
    Represents a single timed step in a hierarchical workflow.
    """
    __slots__ = ("name", "parent", "children", "count", "total_time",
                 "_start_time", "lock")

    def __init__(self, name: str, parent: "StepTimer" = None):
        self.name = name
        self.parent = parent
        self.children = {}       # map step name -> StepTimer
        self.count = 0
        self.total_time = 0.0
        self._start_time = None
        self.lock = threading.RLock()

    def start(self):
        with self.lock:
            self.count += 1
            self._start_time = time.perf_counter()

    def stop(self):
        with self.lock:
            if self._start_time is not None:
                elapsed = time.perf_counter() - self._start_time
                self.total_time += elapsed
                self._start_time = None

    def get_child(self, step_name: str) -> "StepTimer":
        with self.lock:
            if step_name not in self.children:
                self.children[step_name] = StepTimer(step_name, parent=self)
            return self.children[step_name]

    def __repr__(self):
        return f"<StepTimer(name={self.name}, count={self.count}, total={self.total_time:.4f}s)>"


class SpeedAnalyser:
    """
    Manages a root StepTimer and prints hierarchical timing results.
    """
    def __init__(self, root_name="ROOT", print_threshold=0.01):
        self.root = StepTimer(root_name)
        self.print_threshold = print_threshold
        self._root_token = None
        self.running = False

    def start(self):
        """
        Begin timing the root step and set it as the active step in context.
        """
        self.running = True
        self._root_token = current_step_var.set(self.root)
        self.root.start()

    def end(self):
        """
        Stop timing the root step, restore prior context, then print a report.
        """
        self.running = False
        self.root.stop()
        if self._root_token is not None:
            current_step_var.reset(self._root_token)
        self._print_report()

    def _print_report(self):
        total = self.root.total_time
        print("\nPerformance Report")
        print("==================")
        self._print_step(self.root, total, level=0)

    def _print_step(self, step: StepTimer, total: float, level: int):
        fraction = (step.total_time / total) if total > 0 else 0
        if fraction < self.print_threshold and step.parent is not None:
            # skip printing steps under the threshold (except the root)
            return

        indent = "  " * level
        pct_str = f"({fraction*100:5.2f}%)"
        print(f"{indent}- {step.name}: {step.total_time:.4f}s "
              f"[count={step.count}] {pct_str}")

        for child in step.children.values():
            self._print_step(child, total, level=level + 1)


def astep_timer(step_name: str, level: int = 0):
    """
    Decorator to measure an async function's performance under a named step,
    optionally tagged with a 'level'.
    
    Usage:
        @astep_time(step_name="fetch_user_data", level=1)
        async def some_async_func(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            parent_step = current_step_var.get()
            # If we are not inside a SpeedAnalyser context, just run the function.
            if parent_step is None:
                return await func(*args, **kwargs)

            # Create or get a child step, optionally including the level in the name.
            # e.g. you might store level in the step name or ignore it in the name if you prefer.
            decorated_step_name = f"{step_name} [lvl={level}]"
            child_step = parent_step.get_child(decorated_step_name)

            token = current_step_var.set(child_step)
            child_step.start()
            try:
                return await func(*args, **kwargs)
            finally:
                child_step.stop()
                # revert context
                current_step_var.reset(token)
        return wrapper
    return decorator
