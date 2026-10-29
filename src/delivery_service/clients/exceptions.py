from delivery_service.exceptions import DomainError


class ClientError(DomainError):
    code = "external_service_error"

    def __init__(self, message: str = "Something wrong with external service") -> None:
        super().__init__(message)


class ExchangerServiceUnavailableError(ClientError):
    code = "exchanger_service_unavailable"

    def __init__(self, url: str) -> None:
        self.url = url

        super().__init__(f"Exchanger service is unavailable by {url}")


class ExchangerServiceJSONKeyNotFoundError(ClientError):
    code = "exchanger_service_wrong_key"

    def __init__(self, key: str) -> None:
        self.key = key

        super().__init__(f"Wrong json key = {key} from exchanger service")


class ExchangerServiceRateValueError(ClientError):
    code = "exchanger_service_wrong_value"

    def __init__(self, value: str) -> None:
        self.value = value

        super().__init__(f"Rate is not a number: obtained {value}")
