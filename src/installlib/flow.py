from typing import Any

from progress.bar import ChargingBar


class InstallationError(BaseException):
    pass


class ResourceNotFound(BaseException):
    pass


class Sequence:
    def __init__(self, *items, resources=None) -> None:
        self.items = items
        self._is_cancelled = False
        self.bar = ChargingBar("Installing..", max=len(self.items))

    def execute(self):
        for item in self.items:
            if self._is_cancelled:
                break
            self.bar.message = item.name
            self.bar.next()
            success, error = item.execute()

            if not success:
                raise InstallationError(f"Installation of {item} failed. Error: {error}")
        return True, None

    def cancel(self):
        self._is_cancelled = True


class Resource:
    RESOURCES = {}

    def __init__(self, key) -> None:
        self.key = key

    def get(self):
        return self.RESOURCES[self.key]

    def set(self, value):
        self.RESOURCES[self.key] = value

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.get()


def rs(key):
    return Resource(key)
