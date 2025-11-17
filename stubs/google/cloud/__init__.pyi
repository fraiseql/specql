# Type stubs for google.cloud
from typing import Any

class functions_v1:
    class CloudFunctionsServiceClient:
        pass

    class CloudFunctionsServiceAsyncClient:
        def call_function(self, request: Any) -> Any: ...

    class CallFunctionRequest:
        def __init__(self, name: str, data: bytes) -> None: ...
