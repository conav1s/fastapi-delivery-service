class DomainError(Exception):
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(message)
