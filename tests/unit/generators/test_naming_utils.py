"""Tests for naming utility functions"""

import pytest


class TestCamelToSnake:
    """Test camel_to_snake conversion utility"""

    def test_simple_camel_case(self):
        """Simple CamelCase should convert correctly"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("ColorMode") == "color_mode"
        assert camel_to_snake("Contact") == "contact"

    def test_multiple_words(self):
        """Multiple word CamelCase"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("DuplexMode") == "duplex_mode"
        assert camel_to_snake("MachineFunction") == "machine_function"
        assert camel_to_snake("ManufacturerRange") == "manufacturer_range"

    def test_all_caps(self):
        """All caps should stay together"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("URL") == "url"
        assert camel_to_snake("HTTPServer") == "http_server"

    def test_acronym_middle(self):
        """Acronym in middle of name"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("PDFDocument") == "pdf_document"
        assert camel_to_snake("XMLParser") == "xml_parser"

    def test_already_snake_case(self):
        """Already snake_case should pass through"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("color_mode") == "color_mode"
        assert camel_to_snake("duplex_mode") == "duplex_mode"

    def test_numbers(self):
        """Handle numbers in names"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("Product2B") == "product_2_b"
        assert camel_to_snake("Level3Support") == "level_3_support"

    def test_single_word(self):
        """Single word should lowercase"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("Product") == "product"
        assert camel_to_snake("User") == "user"

    def test_edge_cases(self):
        """Edge cases"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("") == ""
        assert camel_to_snake("A") == "a"
        assert camel_to_snake("AB") == "ab"
        assert camel_to_snake("ABC") == "abc"

    def test_complex_cases(self):
        """Complex real-world cases"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("ColorMode") == "color_mode"
        assert camel_to_snake("DuplexMode") == "duplex_mode"
        assert camel_to_snake("MachineFunction") == "machine_function"
        assert camel_to_snake("Manufacturer") == "manufacturer"
        assert camel_to_snake("Model") == "model"
        assert camel_to_snake("Accessory") == "accessory"


class TestAcronymSupport:
    """Test smart acronym preservation"""

    def test_b2b_b2c_acronyms(self):
        """Business model acronyms should be preserved"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("B2BProduct") == "b2b_product"
        assert camel_to_snake("B2CCustomer") == "b2c_customer"
        assert camel_to_snake("P2PTransaction") == "p2p_transaction"
        assert camel_to_snake("C2CMarketplace") == "c2c_marketplace"

    def test_api_protocol_acronyms(self):
        """API and protocol acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("RestAPI") == "rest_api"
        assert camel_to_snake("RestAPIClient") == "rest_api_client"
        assert camel_to_snake("HTTPSConnection") == "https_connection"
        assert camel_to_snake("GraphQLResolver") == "graphql_resolver"

    def test_auth_acronyms(self):
        """Authentication acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("OAuth2Provider") == "oauth2_provider"
        assert camel_to_snake("SSOIntegration") == "sso_integration"
        assert camel_to_snake("JWTToken") == "jwt_token"
        assert camel_to_snake("2FASetup") == "2fa_setup"

    def test_network_acronyms(self):
        """Network and protocol acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("IPv4Address") == "ipv4_address"
        assert camel_to_snake("IPv6Gateway") == "ipv6_gateway"
        assert camel_to_snake("TCPConnection") == "tcp_connection"
        assert camel_to_snake("DNSRecord") == "dns_record"

    def test_business_system_acronyms(self):
        """Business system acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("CRMContact") == "crm_contact"
        assert camel_to_snake("ERPIntegration") == "erp_integration"
        assert camel_to_snake("POSTerminal") == "pos_terminal"
        assert camel_to_snake("SKUInventory") == "sku_inventory"

    def test_custom_acronyms(self):
        """Custom acronyms via preserve_acronyms parameter"""
        from src.generators.naming_utils import camel_to_snake

        # Without custom acronym
        assert camel_to_snake("Product2B") == "product_2_b"

        # With custom acronym
        assert camel_to_snake("Product2B", preserve_acronyms={"2B"}) == "product_2b"

        # Custom business acronym
        assert camel_to_snake("ACMEProduct", preserve_acronyms={"ACME"}) == "acme_product"

    def test_multiple_acronyms(self):
        """Multiple acronyms in one name"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("RestAPIHTTPSClient") == "rest_api_https_client"
        assert camel_to_snake("OAuth2JWTProvider") == "oauth2_jwt_provider"
        assert camel_to_snake("IPv4TCPConnection") == "ipv4_tcp_connection"

    def test_disable_common_acronyms(self):
        """Can disable common acronyms if needed"""
        from src.generators.naming_utils import camel_to_snake

        # With common acronyms (default)
        assert camel_to_snake("B2BProduct") == "b2b_product"

        # Without common acronyms
        assert camel_to_snake("B2BProduct", use_common_acronyms=False) == "b_2_b_product"

    def test_backward_compatibility(self):
        """Regular names still work as before"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("ColorMode") == "color_mode"
        assert camel_to_snake("DuplexMode") == "duplex_mode"
        assert camel_to_snake("MachineFunction") == "machine_function"
        assert camel_to_snake("ManufacturerRange") == "manufacturer_range"
