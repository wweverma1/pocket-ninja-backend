from typing import Any


class Response:
    def __init__(self, errorStatus: int = 0, message: str = "", result: Any = None):
        self.errorStatus = errorStatus
        self.message = message
        self.result = result

    def to_dict(self):
        return {
            "errorStatus": self.errorStatus,
            "message": self.message,
            "result": self.result,
        }
