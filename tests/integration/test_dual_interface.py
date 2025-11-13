"""
Integration tests for dual interface (CLI + GraphQL).

Tests that CLI and GraphQL both work correctly and use the same
application services.
"""
import pytest
import subprocess
# Note: GraphQL client imports commented out until FraiseQL is available
# from gql import gql, Client
# from gql.transport.requests import RequestsHTTPTransport


class TestDualInterface:
    """Test CLI and GraphQL access to same functionality"""

    @pytest.fixture
    def graphql_client(self):
        """GraphQL client for testing"""
        # Note: This will work once FraiseQL is properly configured
        # transport = RequestsHTTPTransport(url='http://localhost:4000/graphql')
        # return Client(transport=transport, fetch_schema_from_transport=True)
        return None  # Placeholder

    def test_register_domain_via_cli_query_via_cli(self):
        """Test registering domain via CLI, querying via CLI"""
        # 1. Register domain via CLI
        result = subprocess.run(
            ['specql', 'domain', 'register', '--number', '20', '--name', 'test_cli', '--schema-type', 'shared'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Domain registered: D20' in result.stdout

        # 2. Query domain via CLI
        result = subprocess.run(
            ['specql', 'domain', 'show', '--number', '20'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'test_cli' in result.stdout
        assert 'D20' in result.stdout

    def test_register_domain_via_graphql_query_via_graphql(self, graphql_client):
        """Test registering domain via GraphQL, querying via GraphQL"""
        # Note: This test requires FraiseQL to be working
        pytest.skip("GraphQL tests require FraiseQL server to be running")

        # Example of what the test would look like:
        # # 1. Register domain via GraphQL
        # mutation = gql('''
        #     mutation {
        #         registerDomain(
        #             domainNumber: 21
        #             domainName: "test_graphql"
        #             schemaType: SHARED
        #         ) {
        #             domainNumber
        #             identifier
        #         }
        #     }
        # ''')
        #
        # result = graphql_client.execute(mutation)
        # assert result['registerDomain']['domainNumber'] == 21
        # assert result['registerDomain']['identifier'] == 'D21'
        #
        # # 2. Query domain via GraphQL
        # query = gql('''
        #     query {
        #         domain(domainNumber: 21) {
        #             domainNumber
        #             domainName
        #             identifier
        #         }
        #     }
        # ''')
        #
        # result = graphql_client.execute(query)
        # assert result['domain']['domainNumber'] == 21
        # assert result['domain']['domainName'] == 'test_graphql'
        # assert result['domain']['identifier'] == 'D21'

    def test_register_domain_via_cli_query_via_graphql(self, graphql_client):
        """Test registering domain via CLI, querying via GraphQL"""
        # 1. Register domain via CLI
        result = subprocess.run(
            ['specql', 'domain', 'register', '--number', '22', '--name', 'cli_to_graphql', '--schema-type', 'shared'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Domain registered: D22' in result.stdout

        # 2. Query domain via GraphQL
        # Note: This would require FraiseQL
        pytest.skip("GraphQL query requires FraiseQL server")

        # Example:
        # query = gql('''
        #     query {
        #         domain(domainNumber: 22) {
        #             domainNumber
        #             domainName
        #             identifier
        #         }
        #     }
        # ''')
        #
        # result = graphql_client.execute(query)
        # assert result['domain']['domainNumber'] == 22
        # assert result['domain']['domainName'] == 'cli_to_graphql'
        # assert result['domain']['identifier'] == 'D22'

    def test_concurrent_access_cli_and_graphql(self, graphql_client):
        """Test concurrent access from CLI and GraphQL"""
        # Note: This test requires both CLI and GraphQL server running
        pytest.skip("Concurrent access test requires both CLI and GraphQL server")

        # Example implementation:
        # import threading
        #
        # cli_result = [None]
        # graphql_result = [None]
        #
        # def register_via_cli():
        #     result = subprocess.run(
        #         ['specql', 'domain', 'register', '--number', '30', '--name', 'concurrent_cli', '--schema-type', 'shared'],
        #         capture_output=True,
        #         text=True
        #     )
        #     cli_result[0] = result.returncode == 0
        #
        # def register_via_graphql():
        #     mutation = gql('''
        #         mutation {
        #             registerDomain(
        #                 domainNumber: 31
        #                 domainName: "concurrent_graphql"
        #                 schemaType: SHARED
        #             ) {
        #                 identifier
        #             }
        #         }
        #     ''')
        #     result = graphql_client.execute(mutation)
        #     graphql_result[0] = result['registerDomain']['identifier'] == 'D31'
        #
        # # Run concurrently
        # t1 = threading.Thread(target=register_via_cli)
        # t2 = threading.Thread(target=register_via_graphql)
        #
        # t1.start()
        # t2.start()
        # t1.join()
        # t2.join()
        #
        # assert cli_result[0] is True
        # assert graphql_result[0] is True