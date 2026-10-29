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
        super().__init__("Cannot obtain exchange rate: cache and CBR are both unavailable")


class SupportNotConfiguredError(DomainError):
    code = "support_not_configured"

    def __init__(self) -> None:
        super().__init__("Support assistant is not configured: GROQ_API_KEY is not set")


class KnowledgeBaseUnavailableError(DomainError):
    code = "knowledge_base_unavailable"

    def __init__(self) -> None:
        super().__init__("Knowledge base search is unavailable")


class LlmUnavailableError(DomainError):
    code = "llm_unavailable"

    def __init__(self) -> None:
        super().__init__("Language model is unavailable or its rate limit is exhausted")


class PackageAlreadyAssignedError(DomainError):
    code = "package_already_assigned"

    def __init__(self, package_id: int) -> None:
        super().__init__(f"Package with id = {package_id} is already assigned")
