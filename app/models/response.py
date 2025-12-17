from typing import Any, Dict


class Response:
    def __init__(self, errorStatus: int = 1, message_en: str = "", message_jp: str = "", result: Any = None):
        self.errorStatus = errorStatus
        self.message_en = message_en
        self.message_jp = message_jp
        self.result = result

    def to_dict(self):
        return {
            "errorStatus": self.errorStatus,
            "message": {
                "en": self.message_en,
                "jp": self.message_jp
            },
            "result": self.result,
        }
