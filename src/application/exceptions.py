"""Application-level exceptions"""


class ApplicationError(Exception):
    """Base exception for application layer"""
    pass


class DomainAlreadyExistsError(ApplicationError):
    """Raised when domain number already exists"""
    def __init__(self, domain_number: int):
        self.domain_number = domain_number
        super().__init__(f"Domain {domain_number} already exists")


class DomainNotFoundError(ApplicationError):
    """Raised when domain not found"""
    def __init__(self, domain_number: int):
        self.domain_number = domain_number
        super().__init__(f"Domain {domain_number} not found")


class SubdomainAlreadyExistsError(ApplicationError):
    """Raised when subdomain already exists in domain"""
    def __init__(self, domain_number: int, subdomain_number: int):
        self.domain_number = domain_number
        self.subdomain_number = subdomain_number
        super().__init__(
            f"Subdomain {subdomain_number} already exists in domain {domain_number}"
        )


class SubdomainNotFoundError(ApplicationError):
    """Raised when subdomain not found"""
    def __init__(self, domain_number: int, subdomain_number: int):
        self.domain_number = domain_number
        self.subdomain_number = subdomain_number
        super().__init__(
            f"Subdomain {subdomain_number} not found in domain {domain_number}"
        )