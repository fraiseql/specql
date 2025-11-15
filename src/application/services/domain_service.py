"""Application Service for Domain operations"""
from typing import List, Optional
from src.domain.repositories.domain_repository import DomainRepository
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber, SubdomainNumber
from src.application.dtos.domain_dto import DomainDTO, SubdomainDTO
from src.application.exceptions import (
    DomainAlreadyExistsError,
    DomainNotFoundError,
    SubdomainAlreadyExistsError
)


class DomainService:
    """
    Application Service for Domain operations

    Uses repository abstraction - doesn't care about storage implementation
    """

    def __init__(self, repository: DomainRepository):
        self.repository = repository

    def register_domain(
        self,
        domain_number: str,
        domain_name: str,
        schema_type: str
    ) -> DomainDTO:
        """
        Register a new domain.

        Args:
            domain_number: Unique domain identifier (00-FF hex)
            domain_name: Human-readable domain name
            schema_type: 'framework', 'multi_tenant', or 'shared'

        Returns:
            DomainDTO with registered domain details

        Raises:
            DomainAlreadyExistsError: If domain_number already exists
            ValueError: If input validation fails
        """
        # Convert to uppercase for consistency
        domain_number = domain_number.upper()

        # Create value object (validates hex range)
        domain_number_vo = DomainNumber(domain_number)

        # Check uniqueness by trying to get the domain
        try:
            self.repository.get(domain_number)
            raise DomainAlreadyExistsError(domain_number)
        except ValueError:
            # Domain doesn't exist, which is what we want
            pass

        # Map schema_type to multi_tenant
        multi_tenant = schema_type == "multi_tenant"

        # Create domain aggregate
        domain = Domain(
            domain_number=domain_number_vo,
            domain_name=domain_name,
            description=None,  # Will be set later if needed
            multi_tenant=multi_tenant,
            aliases=[]
        )

        # Persist
        self.repository.save(domain)

        # Return DTO
        return DomainDTO(
            domain_number=domain.domain_number.value,
            domain_name=domain.domain_name,
            schema_type=schema_type,
            identifier=f"D{domain.domain_number.value}",
            pk_domain=None  # In-memory doesn't have PKs
        )

    def list_domains(
        self,
        schema_type: Optional[str] = None
    ) -> List[DomainDTO]:
        """
        List all domains, optionally filtered by schema_type.

        Args:
            schema_type: Optional filter by schema type

        Returns:
            List of DomainDTO objects
        """
        domains = self.repository.list_all()

        # Filter by schema_type if provided
        if schema_type:
            multi_tenant_filter = schema_type == "multi_tenant"
            domains = [d for d in domains if d.multi_tenant == multi_tenant_filter]

        return [
            DomainDTO(
                domain_number=d.domain_number.value,
                domain_name=d.domain_name,
                schema_type="multi_tenant" if d.multi_tenant else "framework",
                identifier=f"D{d.domain_number.value}",
                pk_domain=None
            )
            for d in domains
        ]

    def get_domain(
        self,
        domain_number: str
    ) -> DomainDTO:
        """
        Get domain by number.

        Args:
            domain_number: Domain identifier (00-FF hex)

        Returns:
            DomainDTO

        Raises:
            DomainNotFoundError: If domain not found
        """
        # Convert to uppercase for consistency
        domain_number = domain_number.upper()

        try:
            domain = self.repository.get(domain_number)
        except ValueError:
            raise DomainNotFoundError(domain_number)

        return DomainDTO(
            domain_number=domain.domain_number.value,
            domain_name=domain.domain_name,
            schema_type="multi_tenant" if domain.multi_tenant else "framework",
            identifier=f"D{domain.domain_number.value}",
            pk_domain=None
        )

    def register_subdomain(
        self,
        parent_domain_number: str,
        subdomain_number: str,
        subdomain_name: str
    ) -> SubdomainDTO:
        """
        Register a new subdomain under a parent domain.

        Args:
            parent_domain_number: Parent domain identifier (00-FF hex)
            subdomain_number: Subdomain identifier (3-digit hex: DDS)
            subdomain_name: Human-readable subdomain name

        Returns:
            SubdomainDTO with registered subdomain details

        Raises:
            DomainNotFoundError: If parent domain doesn't exist
            SubdomainAlreadyExistsError: If subdomain already exists
            ValueError: If input validation fails
        """
        # Convert to uppercase for consistency
        parent_domain_number = parent_domain_number.upper()
        subdomain_number = subdomain_number.upper()

        # Validate parent domain exists
        try:
            parent_domain = self.repository.get(parent_domain_number)
        except ValueError:
            raise DomainNotFoundError(parent_domain_number)

        # Validate subdomain number format
        subdomain_number_vo = SubdomainNumber(subdomain_number)

        # Check that subdomain belongs to the correct parent domain
        if subdomain_number_vo.domain_part != parent_domain_number:
            raise ValueError(
                f"Subdomain {subdomain_number} does not belong to domain {parent_domain_number}"
            )

        # Check uniqueness within domain
        if subdomain_number in parent_domain.subdomains:
            raise SubdomainAlreadyExistsError(parent_domain_number, subdomain_number[-1])

        # Create subdomain aggregate
        subdomain = Subdomain(
            subdomain_number=subdomain_number,
            subdomain_name=subdomain_name,
            description=None  # Will be set later if needed
        )

        # Add to parent domain
        parent_domain.add_subdomain(subdomain)

        # Persist
        self.repository.save(parent_domain)

        # Return DTO
        return SubdomainDTO(
            subdomain_number=subdomain_number,
            subdomain_name=subdomain_name,
            parent_domain_number=parent_domain_number,
            identifier=f"D{parent_domain_number}S{subdomain_number[-1]}",
            pk_subdomain=None  # In-memory doesn't have PKs
        )

    def list_subdomains(
        self,
        parent_domain_number: Optional[str] = None
    ) -> List[SubdomainDTO]:
        """
        List all subdomains, optionally filtered by parent domain.

        Args:
            parent_domain_number: Optional filter by parent domain (00-FF hex)

        Returns:
            List of SubdomainDTO objects
        """
        if parent_domain_number:
            # Convert to uppercase
            parent_domain_number = parent_domain_number.upper()

            # Get specific domain and its subdomains
            try:
                parent_domain = self.repository.get(parent_domain_number)
            except ValueError:
                return []

            subdomains = list(parent_domain.subdomains.values())
            parent_num = parent_domain_number
        else:
            # Get all subdomains from all domains
            all_domains = self.repository.list_all()
            subdomains = []
            for domain in all_domains:
                for subdomain in domain.subdomains.values():
                    subdomains.append(subdomain)
            parent_num = None

        return [
            SubdomainDTO(
                subdomain_number=subdomain.subdomain_number,
                subdomain_name=subdomain.subdomain_name,
                parent_domain_number=parent_num or subdomain.parent_domain_number,
                identifier=f"D{subdomain.parent_domain_number}S{subdomain.subdomain_number[-1]}",
                pk_subdomain=None
            )
            for subdomain in subdomains
        ]

        return DomainDTO(
            domain_number=domain.domain_number.value,
            domain_name=domain.domain_name,
            schema_type="multi_tenant" if domain.multi_tenant else "framework",
            identifier=f"D{domain.domain_number.value}",
            pk_domain=None
        )