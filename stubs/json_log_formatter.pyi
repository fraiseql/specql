# Type stubs for json_log_formatter
from typing import Any
import logging

class JSONFormatter(logging.Formatter):
    def __init__(self) -> None: ...
    def format(self, record: Any) -> str: ...
