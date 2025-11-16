from src.core.specql_parser import SpecQLParser


def test_parse_contact_entity_with_email_phone_rich_types():
    """Contact entity uses email and phone rich types"""
    yaml_content = """
entity: Contact
schema: tenant
fields:
  email_address: email!
  mobile_phone: phone
"""
    result = SpecQLParser().parse(yaml_content)

    # Should recognize 'email' and 'phone' as rich scalar types
    assert result.fields["email_address"].type_name == "email"
    assert result.fields["email_address"].is_rich_type() is True
    assert result.fields["mobile_phone"].type_name == "phone"
