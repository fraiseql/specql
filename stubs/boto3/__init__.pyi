# Type stubs for boto3
from typing import Any

class Session:
    def client(self, service_name: str, **kwargs: Any) -> Any: ...

def client(service_name: str, **kwargs: Any) -> Any: ...
