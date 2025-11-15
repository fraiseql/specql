"""Application Service for Subdomain operations"""
from typing import List, Optional
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Subdomain
from src.application.dtos.domain_dto import SubdomainDTO
from src.application.exceptions import (
    DomainNotFoundError,
    SubdomainAlreadyExistsError
)


class SubdomainService:
    """
    Application Service for Subdomain operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, domain_repository: DomainRepository):
        self.domain_repository = domain_repository

    def register_subdomain(
        self,
        parent_domain_number: int,
        subdomain_number: int,
        subdomain_name: str
    ) -> SubdomainDTO:
        """
        Register a new subdomain under a parent domain.

        Args:
            parent_domain_number: Parent domain identifier
            subdomain_number: Subdomain number within domain (0-99)
            subdomain_name: Human-readable subdomain name

        Returns:
            SubdomainDTO with registered subdomain details

        Raises:
            DomainNotFoundError: If parent domain doesn't exist
            SubdomainAlreadyExistsError: If subdomain already exists
            ValueError: If input validation fails
        """
        # Validate parent domain exists
        parent_domain_number_str = str(parent_domain_number)
        try:
            parent_domain = self.domain_repository.get(parent_domain_number_str)
        except ValueError:
            raise DomainNotFoundError(parent_domain_number)

        # Create subdomain number (2-digit format as used in CLI)
        subdomain_number_str = str(subdomain_number).zfill(2)

        # Check uniqueness within domain
        if subdomain_number_str in parent_domain.subdomains:
            raise SubdomainAlreadyExistsError(parent_domain_number, subdomain_number)

        # Create subdomain aggregate
        subdomain = Subdomain(
            subdomain_number=subdomain_number_str,
            subdomain_name=subdomain_name,
            description=None  # Will be set later if needed
        )

        # Add to parent domain
        parent_domain.add_subdomain(subdomain)

        # Persist
        self.domain_repository.save(parent_domain)

        # Return DTO
        return SubdomainDTO(
            subdomain_number=subdomain_number,
            subdomain_name=subdomain_name,
            parent_domain_number=parent_domain_number,
            identifier=f"D{parent_domain_number}S{subdomain_number}",
            pk_subdomain=None  # In-memory doesn't have PKs
        )

    def list_subdomains(
        self,
        parent_domain_number: Optional[int] = None
    ) -> List[SubdomainDTO]:
        """
        List all subdomains, optionally filtered by parent domain.

        Args:
            parent_domain_number: Optional filter by parent domain

        Returns:
            List of SubdomainDTO objects
        """
        if parent_domain_number:
            # Get specific domain and its subdomains
            parent_domain_number_str = str(parent_domain_number)
            try:
                parent_domain = self.domain_repository.get(parent_domain_number_str)
                subdomains = list(parent_domain.subdomains.values())
                parent_num = int(parent_domain.domain_number.value)
            except ValueError:
                return []  # Domain not found, return empty list

            return [
                SubdomainDTO(
                    subdomain_number=int(s.subdomain_number),
                    subdomain_name=s.subdomain_name,
                    parent_domain_number=parent_num,
                    identifier=f"D{parent_num}S{s.subdomain_number}",
                    pk_subdomain=None
                )
                for s in subdomains
            ]
        else:
            # Get all subdomains from all domains
            domains = self.domain_repository.list_all()
            result = []
            for domain in domains:
                domain_num = int(domain.domain_number.value)
                for subdomain in domain.subdomains.values():
                    result.append(SubdomainDTO(
                        subdomain_number=int(subdomain.subdomain_number),
                        subdomain_name=subdomain.subdomain_name,
                        parent_domain_number=domain_num,
                        identifier=f"D{domain_num}S{subdomain.subdomain_number}",
                        pk_subdomain=None
                    ))
            return result