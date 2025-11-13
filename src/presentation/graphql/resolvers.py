"""
GraphQL resolvers for SpecQL registry.

Each resolver is a thin wrapper calling application services.
"""
from typing import List, Optional
from src.application.services.domain_service import DomainService, DomainNotFoundError
from src.application.services.subdomain_service import SubdomainService, SubdomainNotFoundError
from src.application.services.pattern_service import PatternService, PatternNotFoundError


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
                'patternId': p.pattern_id,
                'patternName': p.pattern_name,
                'category': p.category.upper(),
                'description': p.description,
                'patternType': p.pattern_type.upper(),
                'usageCount': p.usage_count,
                'popularityScore': score
            }
            for p, score in patterns_with_scores
        ]