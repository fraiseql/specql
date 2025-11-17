# Type stubs for pglast
from typing import Any, Dict, List, Union

def parse_sql(sql: str) -> Any: ...

class Node:
    pass

# AST classes
class ast:
    class CreateFunctionStmt:
        funcname: Any
        parameters: Any
        returnType: Any
        options: Any

    class FunctionParameter:
        name: Any
        argType: Any

    class TypeName:
        names: Any

    class DefElem:
        defname: Any
        arg: Any

# Add other common pglast functions/classes as needed
