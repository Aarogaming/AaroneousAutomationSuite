from typing import Any, Callable


class _Logger:
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _fn(*args: Any, **kwargs: Any) -> None:
            return None

        return _fn


logger = _Logger()
