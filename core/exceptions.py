class SpecQLValidationError(Exception):
    """Raised when SpecQL validation fails."""

    def __init__(self, entity: str, message: str):
        self.entity = entity
        self.message = message
        super().__init__(f"Validation error in entity '{entity}': {message}")
