"""
GraphQL resolvers for SpecQL registry.

Each resolver is a thin wrapper calling application services.
"""
from typing import List, Optional
from src.application.services.domain_service import DomainService
from src.application.services.subdomain_service import SubdomainService
from src.application.services.pattern_service import PatternService
from src.application.exceptions import (
    DomainAlreadyExistsError,
    DomainNotFoundError,
    SubdomainAlreadyExistsError
)


class QueryResolvers:
    """Query resolvers"""

    def __init__(
        self,
        domain_service: DomainService,
        subdomain_service: SubdomainService,
        pattern_service: PatternService
    ):
        self.domain_service = domain_service
        self.subdomain_service = subdomain_service
        self.pattern_service = pattern_service

    def domains(self, info, schema_type: Optional[str] = None) -> List[dict]:
        """
        Query: domains(schemaType: SchemaType): [Domain!]!

        List all domains, optionally filtered by schema type.
        """
        domains = self.domain_service.list_domains(schema_type=schema_type)

        return [
            {
                'domainNumber': int(d.domain_number, 16),  # Convert hex to int
                'domainName': d.domain_name,
                'schemaType': d.schema_type.upper(),
                'identifier': d.identifier,
                'description': d.description,
                'createdAt': None  # TODO: Add to DTO
            }
            for d in domains
        ]

    def domain(self, info, domain_number: int) -> Optional[dict]:
        """
        Query: domain(domainNumber: Int!): Domain

        Get single domain by number.
        """
        try:
            # Convert int to hex string
            domain_hex = f"{domain_number:02X}"
            domain = self.domain_service.get_domain(domain_hex)
            return {
                'domainNumber': int(domain.domain_number, 16),
                'domainName': domain.domain_name,
                'schemaType': domain.schema_type.upper(),
                'identifier': domain.identifier,
                'description': domain.description,
                'createdAt': None
            }
        except DomainNotFoundError:
            return None

    def subdomains(self, info, parent_domain_number: Optional[int] = None) -> List[dict]:
        """
        Query: subdomains(parentDomainNumber: Int): [Subdomain!]!

        List all subdomains, optionally filtered by parent domain.
        """
        subdomains = self.subdomain_service.list_subdomains(
            parent_domain_number=parent_domain_number
        )

        return [
            {
                'subdomainNumber': int(s.subdomain_number),
                'subdomainName': s.subdomain_name,
                'parentDomainNumber': int(s.parent_domain_number),
                'identifier': s.identifier,
                'description': s.description,
                'createdAt': None
            }
            for s in subdomains
        ]

    def search_patterns(
        self,
        info,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[dict]:
        """
        Query: searchPatterns(query: String!, limit: Int, minSimilarity: Float): [Pattern!]!

        Semantic search for patterns using natural language.
        """
        patterns_with_scores = self.pattern_service.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=min_similarity
        )

        return [
            {
                'patternId': str(p.id) if p.id else '',
                'patternName': p.name,
                'category': p.category.value.upper(),
                'description': p.description,
                'patternType': 'UNIVERSAL',  # Default for now
                'usageCount': p.times_instantiated,
                'popularityScore': score
            }
            for p, score in patterns_with_scores
        ]


class MutationResolvers:
    """Mutation resolvers"""

    def __init__(
        self,
        domain_service: DomainService,
        subdomain_service: SubdomainService
    ):
        self.domain_service = domain_service
        self.subdomain_service = subdomain_service

    def register_domain(
        self,
        info,
        domain_number: int,
        domain_name: str,
        schema_type: str,
        description: Optional[str] = None
    ) -> dict:
        """
        Mutation: registerDomain(...): Domain!

        Register a new domain.

        Raises:
            GraphQL error if domain already exists
        """
        try:
            # Convert int to hex string
            domain_hex = f"{domain_number:02X}"
            domain = self.domain_service.register_domain(
                domain_number=domain_hex,
                domain_name=domain_name,
                schema_type=schema_type.lower()
            )

            return {
                'domainNumber': int(domain.domain_number, 16),
                'domainName': domain.domain_name,
                'schemaType': domain.schema_type.upper(),
                'identifier': domain.identifier,
                'description': domain.description,
                'createdAt': None
            }

        except DomainAlreadyExistsError as e:
            raise Exception(str(e))  # Will be handled by GraphQL framework
        except ValueError as e:
            raise Exception(f"Invalid input: {e}")

    def register_subdomain(
        self,
        info,
        parent_domain_number: int,
        subdomain_number: int,
        subdomain_name: str,
        description: Optional[str] = None
    ) -> dict:
        """
        Mutation: registerSubdomain(...): Subdomain!

        Register a new subdomain under a parent domain.
        """
        try:
            # Convert parent domain int to hex
            parent_domain_hex = f"{parent_domain_number:02X}"
            # Create subdomain number as 3-digit hex (parent + subdomain)
            subdomain_hex = f"{parent_domain_hex}{subdomain_number:X}"

            subdomain = self.subdomain_service.register_subdomain(
                parent_domain_number=parent_domain_hex,
                subdomain_number=subdomain_hex,
                subdomain_name=subdomain_name
            )

            return {
                'subdomainNumber': subdomain_number,  # Return the simple int
                'subdomainName': subdomain.subdomain_name,
                'parentDomainNumber': parent_domain_number,
                'identifier': subdomain.identifier,
                'description': subdomain.description,
                'createdAt': None
            }

        except (DomainNotFoundError, SubdomainAlreadyExistsError) as e:
            raise Exception(str(e))  # Will be handled by GraphQL framework
        except ValueError as e:
            raise Exception(f"Invalid input: {e}")


class DomainFieldResolvers:
    """Field resolvers for Domain type"""

    def __init__(self, subdomain_service: SubdomainService):
        self.subdomain_service = subdomain_service

    def subdomains(self, domain: dict, info) -> List[dict]:
        """
        Field resolver: Domain.subdomains

        Resolves subdomains field by querying SubdomainService.
        """
        subdomains = self.subdomain_service.list_subdomains(
            parent_domain_number=domain['domainNumber']
        )

        return [
            {
                'subdomainNumber': int(s.subdomain_number),
                'subdomainName': s.subdomain_name,
                'parentDomainNumber': int(s.parent_domain_number),
                'identifier': s.identifier,
                'description': s.description
            }
            for s in subdomains
        ]


class SubdomainFieldResolvers:
    """Field resolvers for Subdomain type"""

    def __init__(self, domain_service: DomainService):
        self.domain_service = domain_service

    def parent_domain(self, subdomain: dict, info) -> dict:
        """
        Field resolver: Subdomain.parentDomain

        Resolves parent domain field.
        """
        domain = self.domain_service.get_domain(f"{subdomain['parentDomainNumber']:02X}")

        return {
            'domainNumber': int(domain.domain_number, 16),
            'domainName': domain.domain_name,
            'schemaType': domain.schema_type.upper(),
            'identifier': domain.identifier,
            'description': domain.description
        }