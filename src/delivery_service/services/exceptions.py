from delivery_service.exceptions import DomainError


class PackageNotFoundError(DomainError):
    code = "package_not_found"

    def __init__(self, package_id: int) -> None:
        self.package_id = package_id

        super().__init__(f"Package with id = {package_id} not found")


class PackageTypeNotFoundError(DomainError):
    code = "package_type_not_found"

    def __init__(self, type_id: int) -> None:
        self.type_id = type_id

        super().__init__(f"Package Type with id = {type_id} not found")


class ExchangeRateUnavailableError(DomainError):
    code = "rate_unavailable"

    def __init__(self) -> None:
        super().__init__("Cannot obtained rate in any ways")
