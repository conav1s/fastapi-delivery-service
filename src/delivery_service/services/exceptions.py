class PackageNotFoundError(Exception):
    def __init__(self, package_id: int) -> None:
        self.package_id = package_id
        self.message = f"Package with id = {package_id} not found"

        super().__init__(self.message)
